"""
LangSwarm V2 Cost Tracker

Real-time cost tracking system with comprehensive cost monitoring,
categorization, and historical analysis capabilities.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, deque
import json
import csv
import io

from .interfaces import (
    ICostTracker, CostEntry, CostSummary, CostCategory,
    CostTrackingError
)


class CostTracker(ICostTracker):
    """
    Comprehensive cost tracking system for V2 agents.
    
    Provides real-time cost tracking, categorization, and analysis
    with support for multiple providers, models, and usage patterns.
    """
    
    def __init__(self, storage_backend: str = "memory", config: Dict[str, Any] = None):
        """
        Initialize cost tracker.
        
        Args:
            storage_backend: Storage backend ("memory", "sqlite", "redis")
            config: Configuration options
        """
        self._config = config or {}
        self._storage_backend = storage_backend
        
        # In-memory storage (for memory backend or caching)
        self._cost_entries: List[CostEntry] = []
        self._cost_index: Dict[str, List[int]] = defaultdict(list)  # provider -> entry indices
        self._model_index: Dict[str, List[int]] = defaultdict(list)  # model -> entry indices
        self._category_index: Dict[CostCategory, List[int]] = defaultdict(list)
        self._user_index: Dict[str, List[int]] = defaultdict(list)
        
        # Real-time statistics
        self._realtime_stats = {
            "total_cost": 0.0,
            "total_requests": 0,
            "total_tokens": 0,
            "last_update": datetime.utcnow()
        }
        
        # Provider pricing cache
        self._provider_pricing = self._load_provider_pricing()
        
        logging.info(f"Initialized Cost Tracker with {storage_backend} backend")
    
    def _load_provider_pricing(self) -> Dict[str, Dict[str, Any]]:
        """Load provider pricing information"""
        # Current pricing as of late 2024 (approximate)
        return {
            "openai": {
                "gpt-4o": {"input": 0.0025, "output": 0.01},
                "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
                "gpt-4-turbo": {"input": 0.01, "output": 0.03},
                "gpt-4": {"input": 0.03, "output": 0.06},
                "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
                "text-embedding-3-small": {"input": 0.00002, "output": 0.0},
                "text-embedding-3-large": {"input": 0.00013, "output": 0.0},
                "whisper-1": {"input": 0.006, "output": 0.0},  # per minute
                "tts-1": {"input": 0.015, "output": 0.0},      # per 1K characters
                "dalle-3": {"input": 0.04, "output": 0.0}     # per image (standard)
            },
            "anthropic": {
                "claude-3-5-sonnet-20241022": {"input": 0.003, "output": 0.015},
                "claude-3-5-haiku-20241022": {"input": 0.00025, "output": 0.00125},
                "claude-3-opus-20240229": {"input": 0.015, "output": 0.075},
                "claude-3-sonnet-20240229": {"input": 0.003, "output": 0.015},
                "claude-3-haiku-20240307": {"input": 0.00025, "output": 0.00125}
            },
            "gemini": {
                "gemini-pro": {"input": 0.0005, "output": 0.0015},
                "gemini-pro-vision": {"input": 0.00025, "output": 0.0005},
                "gemini-ultra": {"input": 0.0125, "output": 0.0375}
            },
            "cohere": {
                "command-r-plus": {"input": 0.003, "output": 0.015},
                "command-r": {"input": 0.0005, "output": 0.0015},
                "command": {"input": 0.001, "output": 0.002},
                "embed-english-v3.0": {"input": 0.0001, "output": 0.0},
                "embed-multilingual-v3.0": {"input": 0.0001, "output": 0.0}
            },
            "mistral": {
                "mixtral-8x7b-instruct": {"input": 0.0007, "output": 0.0007},
                "mixtral-8x22b-instruct": {"input": 0.002, "output": 0.006},
                "mistral-large": {"input": 0.004, "output": 0.012},
                "mistral-medium": {"input": 0.0027, "output": 0.0081},
                "mistral-small": {"input": 0.0006, "output": 0.0018},
                "mistral-tiny": {"input": 0.00025, "output": 0.00025}
            },
            "huggingface": {
                # Hugging Face Inference API pricing (approximate)
                "default": {"input": 0.0002, "output": 0.0006}
            },
            "local": {
                # Local models have no API cost
                "default": {"input": 0.0, "output": 0.0}
            }
        }
    
    async def track_cost(self, entry: CostEntry) -> None:
        """
        Track a cost entry.
        
        Args:
            entry: Cost entry to track
        """
        try:
            # Validate entry
            if not entry.provider or not entry.model:
                raise CostTrackingError("Provider and model are required")
            
            if entry.amount < 0:
                raise CostTrackingError("Cost amount cannot be negative")
            
            # Calculate derived fields if not provided
            if entry.total_tokens == 0 and entry.input_tokens > 0 and entry.output_tokens > 0:
                entry.total_tokens = entry.input_tokens + entry.output_tokens
            
            # Estimate cost if not provided
            if entry.amount == 0.0 and entry.input_tokens > 0 and entry.output_tokens > 0:
                entry.amount = self._estimate_cost(entry.provider, entry.model, 
                                                 entry.input_tokens, entry.output_tokens)
            
            # Store entry
            entry_index = len(self._cost_entries)
            self._cost_entries.append(entry)
            
            # Update indices
            self._cost_index[entry.provider].append(entry_index)
            self._model_index[entry.model].append(entry_index)
            self._category_index[entry.category].append(entry_index)
            
            if entry.user_id:
                self._user_index[entry.user_id].append(entry_index)
            
            # Update real-time statistics
            self._realtime_stats["total_cost"] += entry.amount
            self._realtime_stats["total_requests"] += entry.requests
            self._realtime_stats["total_tokens"] += entry.total_tokens
            self._realtime_stats["last_update"] = datetime.utcnow()
            
            # Store to persistent backend if configured
            await self._store_to_backend(entry)
            
            logging.debug(f"Tracked cost entry: {entry.entry_id} - ${entry.amount:.4f}")
            
        except Exception as e:
            logging.error(f"Failed to track cost entry: {e}")
            raise CostTrackingError(f"Cost tracking failed: {e}")
    
    def _estimate_cost(self, provider: str, model: str, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost based on token usage"""
        provider_pricing = self._provider_pricing.get(provider.lower(), {})
        
        # Try exact model match first
        model_pricing = provider_pricing.get(model)
        
        # Fall back to default pricing for provider
        if not model_pricing:
            model_pricing = provider_pricing.get("default", {"input": 0.001, "output": 0.003})
        
        # Calculate cost (pricing is per 1K tokens)
        input_cost = (input_tokens / 1000) * model_pricing["input"]
        output_cost = (output_tokens / 1000) * model_pricing["output"]
        
        return input_cost + output_cost
    
    async def _store_to_backend(self, entry: CostEntry) -> None:
        """Store entry to persistent backend"""
        if self._storage_backend == "memory":
            # Already stored in memory
            return
        elif self._storage_backend == "sqlite":
            await self._store_to_sqlite(entry)
        elif self._storage_backend == "redis":
            await self._store_to_redis(entry)
    
    async def _store_to_sqlite(self, entry: CostEntry) -> None:
        """Store entry to SQLite database"""
        # Implementation would use aiosqlite
        pass
    
    async def _store_to_redis(self, entry: CostEntry) -> None:
        """Store entry to Redis"""
        # Implementation would use aioredis
        pass
    
    async def get_cost_summary(self, provider: Optional[str] = None,
                             start_date: Optional[datetime] = None,
                             end_date: Optional[datetime] = None) -> CostSummary:
        """
        Get cost summary for a period.
        
        Args:
            provider: Filter by provider
            start_date: Start date for summary
            end_date: End date for summary
            
        Returns:
            Cost summary
        """
        try:
            # Set default date range if not provided
            if not end_date:
                end_date = datetime.utcnow()
            if not start_date:
                start_date = end_date - timedelta(days=1)  # Last 24 hours
            
            # Filter entries
            filtered_entries = self._filter_entries(provider, start_date, end_date)
            
            if not filtered_entries:
                return CostSummary(
                    period_start=start_date,
                    period_end=end_date,
                    total_cost=0.0
                )
            
            # Calculate summary statistics
            summary = CostSummary(
                period_start=start_date,
                period_end=end_date
            )
            
            # Aggregate costs
            for entry in filtered_entries:
                summary.total_cost += entry.amount
                summary.total_requests += entry.requests
                summary.total_tokens += entry.total_tokens
                summary.total_input_tokens += entry.input_tokens
                summary.total_output_tokens += entry.output_tokens
                
                # Provider breakdown
                if entry.provider not in summary.provider_costs:
                    summary.provider_costs[entry.provider] = 0.0
                summary.provider_costs[entry.provider] += entry.amount
                
                # Model breakdown
                model_key = f"{entry.provider}:{entry.model}"
                if model_key not in summary.model_costs:
                    summary.model_costs[model_key] = 0.0
                summary.model_costs[model_key] += entry.amount
                
                # Category breakdown
                if entry.category not in summary.category_costs:
                    summary.category_costs[entry.category] = 0.0
                summary.category_costs[entry.category] += entry.amount
            
            # Calculate derived metrics (done in __post_init__)
            summary.__post_init__()
            
            # Calculate trends
            summary.cost_trend = await self._calculate_cost_trend(provider, start_date, end_date)
            summary.usage_trend = await self._calculate_usage_trend(provider, start_date, end_date)
            
            return summary
            
        except Exception as e:
            logging.error(f"Failed to get cost summary: {e}")
            raise CostTrackingError(f"Cost summary generation failed: {e}")
    
    def _filter_entries(self, provider: Optional[str], start_date: datetime, end_date: datetime) -> List[CostEntry]:
        """Filter cost entries based on criteria"""
        filtered = []
        
        for entry in self._cost_entries:
            # Check date range
            if entry.timestamp < start_date or entry.timestamp > end_date:
                continue
            
            # Check provider filter
            if provider and entry.provider != provider:
                continue
            
            filtered.append(entry)
        
        return filtered
    
    async def _calculate_cost_trend(self, provider: Optional[str], start_date: datetime, end_date: datetime) -> str:
        """Calculate cost trend over the period"""
        # Split period in half and compare
        mid_date = start_date + (end_date - start_date) / 2
        
        first_half_entries = self._filter_entries(provider, start_date, mid_date)
        second_half_entries = self._filter_entries(provider, mid_date, end_date)
        
        first_half_cost = sum(entry.amount for entry in first_half_entries)
        second_half_cost = sum(entry.amount for entry in second_half_entries)
        
        if first_half_cost == 0:
            return "stable" if second_half_cost == 0 else "increasing"
        
        change_ratio = second_half_cost / first_half_cost
        
        if change_ratio > 1.2:
            return "increasing"
        elif change_ratio < 0.8:
            return "decreasing"
        else:
            return "stable"
    
    async def _calculate_usage_trend(self, provider: Optional[str], start_date: datetime, end_date: datetime) -> str:
        """Calculate usage trend over the period"""
        # Similar to cost trend but for token usage
        mid_date = start_date + (end_date - start_date) / 2
        
        first_half_entries = self._filter_entries(provider, start_date, mid_date)
        second_half_entries = self._filter_entries(provider, mid_date, end_date)
        
        first_half_tokens = sum(entry.total_tokens for entry in first_half_entries)
        second_half_tokens = sum(entry.total_tokens for entry in second_half_entries)
        
        if first_half_tokens == 0:
            return "stable" if second_half_tokens == 0 else "increasing"
        
        change_ratio = second_half_tokens / first_half_tokens
        
        if change_ratio > 1.2:
            return "increasing"
        elif change_ratio < 0.8:
            return "decreasing"
        else:
            return "stable"
    
    async def get_costs_by_provider(self, start_date: Optional[datetime] = None,
                                  end_date: Optional[datetime] = None) -> Dict[str, float]:
        """
        Get costs grouped by provider.
        
        Args:
            start_date: Start date for filtering
            end_date: End date for filtering
            
        Returns:
            Dictionary mapping provider to total cost
        """
        summary = await self.get_cost_summary(None, start_date, end_date)
        return summary.provider_costs
    
    async def get_costs_by_model(self, provider: Optional[str] = None,
                               start_date: Optional[datetime] = None,
                               end_date: Optional[datetime] = None) -> Dict[str, float]:
        """
        Get costs grouped by model.
        
        Args:
            provider: Filter by provider
            start_date: Start date for filtering
            end_date: End date for filtering
            
        Returns:
            Dictionary mapping model to total cost
        """
        summary = await self.get_cost_summary(provider, start_date, end_date)
        return summary.model_costs
    
    async def export_cost_data(self, format: str = "csv",
                             start_date: Optional[datetime] = None,
                             end_date: Optional[datetime] = None) -> str:
        """
        Export cost data in specified format.
        
        Args:
            format: Export format ("csv", "json", "xlsx")
            start_date: Start date for export
            end_date: End date for export
            
        Returns:
            Exported data as string
        """
        try:
            # Set default date range
            if not end_date:
                end_date = datetime.utcnow()
            if not start_date:
                start_date = end_date - timedelta(days=30)  # Last 30 days
            
            # Filter entries
            filtered_entries = self._filter_entries(None, start_date, end_date)
            
            if format.lower() == "csv":
                return self._export_csv(filtered_entries)
            elif format.lower() == "json":
                return self._export_json(filtered_entries)
            elif format.lower() == "xlsx":
                return self._export_xlsx(filtered_entries)
            else:
                raise CostTrackingError(f"Unsupported export format: {format}")
                
        except Exception as e:
            logging.error(f"Failed to export cost data: {e}")
            raise CostTrackingError(f"Cost data export failed: {e}")
    
    def _export_csv(self, entries: List[CostEntry]) -> str:
        """Export entries as CSV"""
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow([
            'entry_id', 'timestamp', 'provider', 'model', 'category',
            'amount', 'currency', 'input_tokens', 'output_tokens', 'total_tokens',
            'requests', 'user_id', 'session_id', 'project_id', 'department'
        ])
        
        # Data rows
        for entry in entries:
            writer.writerow([
                entry.entry_id,
                entry.timestamp.isoformat(),
                entry.provider,
                entry.model,
                entry.category.value,
                entry.amount,
                entry.currency,
                entry.input_tokens,
                entry.output_tokens,
                entry.total_tokens,
                entry.requests,
                entry.user_id or '',
                entry.session_id or '',
                entry.project_id or '',
                entry.department or ''
            ])
        
        return output.getvalue()
    
    def _export_json(self, entries: List[CostEntry]) -> str:
        """Export entries as JSON"""
        data = []
        for entry in entries:
            data.append({
                'entry_id': entry.entry_id,
                'timestamp': entry.timestamp.isoformat(),
                'provider': entry.provider,
                'model': entry.model,
                'category': entry.category.value,
                'amount': entry.amount,
                'currency': entry.currency,
                'input_tokens': entry.input_tokens,
                'output_tokens': entry.output_tokens,
                'total_tokens': entry.total_tokens,
                'requests': entry.requests,
                'user_id': entry.user_id,
                'session_id': entry.session_id,
                'project_id': entry.project_id,
                'department': entry.department,
                'cost_per_token': entry.cost_per_token,
                'cost_per_request': entry.cost_per_request,
                'metadata': entry.metadata,
                'tags': entry.tags
            })
        
        return json.dumps(data, indent=2, default=str)
    
    def _export_xlsx(self, entries: List[CostEntry]) -> str:
        """Export entries as XLSX (would require openpyxl)"""
        # For now, return CSV format
        # In production, this would create an actual Excel file
        return self._export_csv(entries)
    
    async def get_realtime_stats(self) -> Dict[str, Any]:
        """Get real-time cost statistics"""
        return {
            **self._realtime_stats,
            "entries_count": len(self._cost_entries),
            "providers_count": len(self._cost_index),
            "models_count": len(self._model_index),
            "average_cost_per_request": (
                self._realtime_stats["total_cost"] / self._realtime_stats["total_requests"]
                if self._realtime_stats["total_requests"] > 0 else 0.0
            ),
            "average_cost_per_token": (
                self._realtime_stats["total_cost"] / self._realtime_stats["total_tokens"]
                if self._realtime_stats["total_tokens"] > 0 else 0.0
            )
        }
    
    async def get_top_spenders(self, metric: str = "cost", limit: int = 10) -> List[Dict[str, Any]]:
        """Get top spenders by various metrics"""
        if metric == "cost":
            # Group by user_id
            user_costs = defaultdict(float)
            for entry in self._cost_entries:
                if entry.user_id:
                    user_costs[entry.user_id] += entry.amount
            
            sorted_users = sorted(user_costs.items(), key=lambda x: x[1], reverse=True)
            return [{"user_id": user, "total_cost": cost} for user, cost in sorted_users[:limit]]
        
        elif metric == "tokens":
            # Group by user_id
            user_tokens = defaultdict(int)
            for entry in self._cost_entries:
                if entry.user_id:
                    user_tokens[entry.user_id] += entry.total_tokens
            
            sorted_users = sorted(user_tokens.items(), key=lambda x: x[1], reverse=True)
            return [{"user_id": user, "total_tokens": tokens} for user, tokens in sorted_users[:limit]]
        
        else:
            raise CostTrackingError(f"Unsupported metric: {metric}")


class RealTimeCostTracker(CostTracker):
    """
    Real-time cost tracker with streaming capabilities.
    
    Extends the base cost tracker with real-time notifications,
    streaming updates, and immediate cost alerts.
    """
    
    def __init__(self, **kwargs):
        """Initialize real-time cost tracker"""
        super().__init__(**kwargs)
        self._subscribers: List[callable] = []
        self._cost_stream: deque = deque(maxlen=1000)
        self._alert_thresholds = {
            "hourly_spend": 100.0,
            "daily_spend": 1000.0,
            "unusual_spike": 0.5  # 50% increase threshold
        }
    
    async def track_cost(self, entry: CostEntry) -> None:
        """Track cost with real-time notifications"""
        await super().track_cost(entry)
        
        # Add to real-time stream
        self._cost_stream.append({
            "timestamp": entry.timestamp,
            "provider": entry.provider,
            "model": entry.model,
            "amount": entry.amount,
            "tokens": entry.total_tokens
        })
        
        # Check for alerts
        await self._check_realtime_alerts(entry)
        
        # Notify subscribers
        await self._notify_subscribers(entry)
    
    async def _check_realtime_alerts(self, entry: CostEntry) -> None:
        """Check for real-time cost alerts"""
        now = datetime.utcnow()
        
        # Check hourly spend
        hour_ago = now - timedelta(hours=1)
        hourly_entries = [e for e in self._cost_entries if e.timestamp >= hour_ago]
        hourly_spend = sum(e.amount for e in hourly_entries)
        
        if hourly_spend > self._alert_thresholds["hourly_spend"]:
            await self._trigger_alert("hourly_spend_exceeded", {
                "amount": hourly_spend,
                "threshold": self._alert_thresholds["hourly_spend"]
            })
        
        # Check daily spend
        day_ago = now - timedelta(days=1)
        daily_entries = [e for e in self._cost_entries if e.timestamp >= day_ago]
        daily_spend = sum(e.amount for e in daily_entries)
        
        if daily_spend > self._alert_thresholds["daily_spend"]:
            await self._trigger_alert("daily_spend_exceeded", {
                "amount": daily_spend,
                "threshold": self._alert_thresholds["daily_spend"]
            })
    
    async def _trigger_alert(self, alert_type: str, data: Dict[str, Any]) -> None:
        """Trigger a cost alert"""
        alert = {
            "type": alert_type,
            "timestamp": datetime.utcnow(),
            "data": data
        }
        
        logging.warning(f"Cost alert triggered: {alert_type} - {data}")
        
        # Notify subscribers
        for subscriber in self._subscribers:
            try:
                if asyncio.iscoroutinefunction(subscriber):
                    await subscriber(alert)
                else:
                    subscriber(alert)
            except Exception as e:
                logging.error(f"Error notifying subscriber: {e}")
    
    async def _notify_subscribers(self, entry: CostEntry) -> None:
        """Notify real-time subscribers of new cost entry"""
        for subscriber in self._subscribers:
            try:
                if asyncio.iscoroutinefunction(subscriber):
                    await subscriber(entry)
                else:
                    subscriber(entry)
            except Exception as e:
                logging.error(f"Error notifying subscriber: {e}")
    
    def subscribe(self, callback: callable) -> None:
        """Subscribe to real-time cost updates"""
        self._subscribers.append(callback)
    
    def unsubscribe(self, callback: callable) -> None:
        """Unsubscribe from real-time cost updates"""
        if callback in self._subscribers:
            self._subscribers.remove(callback)
    
    async def get_cost_stream(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent cost stream data"""
        return list(self._cost_stream)[-limit:]


# Factory function for creating cost trackers
def create_cost_tracker(tracker_type: str = "standard", **kwargs) -> ICostTracker:
    """
    Create a cost tracker instance.
    
    Args:
        tracker_type: Type of tracker ("standard", "realtime")
        **kwargs: Configuration options
        
    Returns:
        Cost tracker instance
    """
    if tracker_type == "realtime":
        return RealTimeCostTracker(**kwargs)
    else:
        return CostTracker(**kwargs)
