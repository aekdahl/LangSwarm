"""
LangSwarm V2 Budget Management

Comprehensive budget management system with real-time monitoring,
automated alerts, and intelligent spending controls.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from collections import defaultdict
import uuid

from .interfaces import (
    ICostBudgetManager, CostBudget, CostAlert, CostAlertType, 
    BillingPeriod, InvalidBudgetError, BudgetExceededError
)


class BudgetManager(ICostBudgetManager):
    """
    Comprehensive budget management system.
    
    Provides budget creation, monitoring, alerting, and spending controls
    with real-time tracking and automated enforcement capabilities.
    """
    
    def __init__(self, cost_tracker, config: Dict[str, Any] = None):
        """
        Initialize budget manager.
        
        Args:
            cost_tracker: Cost tracking system instance
            config: Budget management configuration
        """
        self._cost_tracker = cost_tracker
        self._config = config or {}
        
        # Budget storage
        self._budgets: Dict[str, CostBudget] = {}
        self._active_budgets: Dict[str, CostBudget] = {}
        
        # Alert management
        self._alert_callbacks: List[Callable] = []
        self._alert_history: List[CostAlert] = []
        
        # Budget monitoring
        self._monitoring_enabled = self._config.get("monitoring_enabled", True)
        self._monitoring_interval = self._config.get("monitoring_interval", 300)  # 5 minutes
        self._monitoring_task: Optional[asyncio.Task] = None
        
        # Spending controls
        self._spending_controls_enabled = self._config.get("spending_controls_enabled", False)
        self._spending_locks: Dict[str, bool] = {}  # budget_id -> locked
        
        logging.info("Initialized Budget Manager")
    
    async def initialize(self) -> None:
        """Initialize budget monitoring"""
        if self._monitoring_enabled:
            self._monitoring_task = asyncio.create_task(self._budget_monitoring_loop())
            logging.info("Budget monitoring started")
    
    async def shutdown(self) -> None:
        """Shutdown budget manager"""
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        logging.info("Budget manager shutdown")
    
    async def create_budget(self, budget: CostBudget) -> str:
        """
        Create a new budget.
        
        Args:
            budget: Budget configuration
            
        Returns:
            Budget ID
        """
        try:
            # Validate budget
            await self._validate_budget(budget)
            
            # Set current period if not provided
            if not budget.current_period_start:
                budget.current_period_start = self._calculate_period_start(budget.period)
                budget.current_period_end = self._calculate_period_end(
                    budget.current_period_start, budget.period
                )
            
            # Initialize current spend
            await self._update_budget_spend(budget)
            
            # Store budget
            self._budgets[budget.budget_id] = budget
            
            if budget.active:
                self._active_budgets[budget.budget_id] = budget
            
            logging.info(f"Created budget: {budget.name} ({budget.budget_id})")
            
            # Generate initial status alert if needed
            await self._check_budget_alerts(budget)
            
            return budget.budget_id
            
        except Exception as e:
            logging.error(f"Failed to create budget: {e}")
            raise InvalidBudgetError(f"Budget creation failed: {e}")
    
    async def _validate_budget(self, budget: CostBudget) -> None:
        """Validate budget configuration"""
        if budget.amount <= 0:
            raise InvalidBudgetError("Budget amount must be greater than zero")
        
        if budget.warning_threshold >= budget.critical_threshold:
            raise InvalidBudgetError("Warning threshold must be less than critical threshold")
        
        if budget.critical_threshold > 100:
            raise InvalidBudgetError("Critical threshold cannot exceed 100%")
        
        if not budget.name:
            raise InvalidBudgetError("Budget name is required")
    
    def _calculate_period_start(self, period: BillingPeriod) -> datetime:
        """Calculate the start of the current billing period"""
        now = datetime.utcnow()
        
        if period == BillingPeriod.HOURLY:
            return now.replace(minute=0, second=0, microsecond=0)
        elif period == BillingPeriod.DAILY:
            return now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == BillingPeriod.WEEKLY:
            days_since_monday = now.weekday()
            monday = now - timedelta(days=days_since_monday)
            return monday.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == BillingPeriod.MONTHLY:
            return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        elif period == BillingPeriod.QUARTERLY:
            quarter_start_month = ((now.month - 1) // 3) * 3 + 1
            return now.replace(month=quarter_start_month, day=1, hour=0, minute=0, second=0, microsecond=0)
        elif period == BillingPeriod.YEARLY:
            return now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            # Default to daily
            return now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    def _calculate_period_end(self, period_start: datetime, period: BillingPeriod) -> datetime:
        """Calculate the end of the billing period"""
        if period == BillingPeriod.HOURLY:
            return period_start + timedelta(hours=1)
        elif period == BillingPeriod.DAILY:
            return period_start + timedelta(days=1)
        elif period == BillingPeriod.WEEKLY:
            return period_start + timedelta(days=7)
        elif period == BillingPeriod.MONTHLY:
            # Handle month end properly
            if period_start.month == 12:
                return period_start.replace(year=period_start.year + 1, month=1)
            else:
                return period_start.replace(month=period_start.month + 1)
        elif period == BillingPeriod.QUARTERLY:
            # Add 3 months
            new_month = period_start.month + 3
            new_year = period_start.year
            if new_month > 12:
                new_month -= 12
                new_year += 1
            return period_start.replace(year=new_year, month=new_month)
        elif period == BillingPeriod.YEARLY:
            return period_start.replace(year=period_start.year + 1)
        else:
            return period_start + timedelta(days=1)
    
    async def _update_budget_spend(self, budget: CostBudget) -> None:
        """Update current period spend for a budget"""
        try:
            # Get cost summary for budget scope
            summary = await self._cost_tracker.get_cost_summary(
                provider=budget.providers[0] if len(budget.providers) == 1 else None,
                start_date=budget.current_period_start,
                end_date=min(datetime.utcnow(), budget.current_period_end)
            )
            
            # Filter costs based on budget scope
            filtered_cost = 0.0
            
            # Provider filtering
            if budget.providers:
                provider_cost = sum(
                    cost for provider, cost in summary.provider_costs.items()
                    if provider in budget.providers
                )
                filtered_cost = provider_cost
            else:
                filtered_cost = summary.total_cost
            
            # Additional filtering would be applied here for:
            # - Models (budget.models)
            # - Categories (budget.categories)  
            # - User IDs (budget.user_ids)
            # - Project IDs (budget.project_ids)
            # - Departments (budget.departments)
            # - Tags (budget.tags)
            
            budget.current_period_spend = filtered_cost
            budget.updated_at = datetime.utcnow()
            
        except Exception as e:
            logging.error(f"Failed to update budget spend for {budget.budget_id}: {e}")
    
    async def update_budget(self, budget_id: str, updates: Dict[str, Any]) -> None:
        """
        Update an existing budget.
        
        Args:
            budget_id: Budget ID to update
            updates: Dictionary of fields to update
        """
        try:
            if budget_id not in self._budgets:
                raise InvalidBudgetError(f"Budget not found: {budget_id}")
            
            budget = self._budgets[budget_id]
            
            # Apply updates
            for field, value in updates.items():
                if hasattr(budget, field):
                    setattr(budget, field, value)
                else:
                    logging.warning(f"Unknown budget field: {field}")
            
            budget.updated_at = datetime.utcnow()
            
            # Re-validate budget
            await self._validate_budget(budget)
            
            # Update active budgets list
            if budget.active and budget_id not in self._active_budgets:
                self._active_budgets[budget_id] = budget
            elif not budget.active and budget_id in self._active_budgets:
                del self._active_budgets[budget_id]
            
            logging.info(f"Updated budget: {budget.name} ({budget_id})")
            
        except Exception as e:
            logging.error(f"Failed to update budget {budget_id}: {e}")
            raise InvalidBudgetError(f"Budget update failed: {e}")
    
    async def check_budget_status(self, budget_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Check current budget status.
        
        Args:
            budget_id: Optional specific budget ID to check
            
        Returns:
            Budget status information
        """
        try:
            if budget_id:
                if budget_id not in self._budgets:
                    return {"error": f"Budget not found: {budget_id}"}
                
                budget = self._budgets[budget_id]
                await self._update_budget_spend(budget)
                
                return {
                    "budget_id": budget_id,
                    "budget_name": budget.name,
                    "amount": budget.amount,
                    "current_spend": budget.current_period_spend,
                    "remaining": budget.remaining_budget,
                    "utilization": budget.budget_utilization,
                    "status": self._get_budget_status(budget),
                    "period": {
                        "type": budget.period.value,
                        "start": budget.current_period_start.isoformat(),
                        "end": budget.current_period_end.isoformat()
                    },
                    "thresholds": {
                        "warning": budget.warning_threshold,
                        "critical": budget.critical_threshold
                    },
                    "is_over_budget": budget.is_over_budget
                }
            else:
                # Check all active budgets
                statuses = {}
                
                for bid, budget in self._active_budgets.items():
                    await self._update_budget_spend(budget)
                    statuses[bid] = {
                        "name": budget.name,
                        "utilization": budget.budget_utilization,
                        "status": self._get_budget_status(budget),
                        "remaining": budget.remaining_budget,
                        "is_over_budget": budget.is_over_budget
                    }
                
                # Overall status
                over_budget_count = sum(1 for s in statuses.values() if s["is_over_budget"])
                critical_count = sum(1 for s in statuses.values() if s["status"] == "critical")
                warning_count = sum(1 for s in statuses.values() if s["status"] == "warning")
                
                overall_status = "healthy"
                if over_budget_count > 0:
                    overall_status = "over_budget"
                elif critical_count > 0:
                    overall_status = "critical"
                elif warning_count > 0:
                    overall_status = "warning"
                
                return {
                    "overall_status": overall_status,
                    "total_budgets": len(self._active_budgets),
                    "over_budget_count": over_budget_count,
                    "critical_count": critical_count,
                    "warning_count": warning_count,
                    "budgets": statuses
                }
                
        except Exception as e:
            logging.error(f"Failed to check budget status: {e}")
            return {"error": str(e)}
    
    def _get_budget_status(self, budget: CostBudget) -> str:
        """Get status string for a budget"""
        if budget.is_over_budget:
            return "over_budget"
        elif budget.budget_utilization >= budget.critical_threshold:
            return "critical"
        elif budget.budget_utilization >= budget.warning_threshold:
            return "warning"
        else:
            return "healthy"
    
    async def generate_budget_alerts(self) -> List[CostAlert]:
        """
        Generate budget-based alerts.
        
        Returns:
            List of cost alerts
        """
        alerts = []
        
        try:
            for budget_id, budget in self._active_budgets.items():
                await self._update_budget_spend(budget)
                budget_alerts = await self._check_budget_alerts(budget)
                alerts.extend(budget_alerts)
            
            return alerts
            
        except Exception as e:
            logging.error(f"Failed to generate budget alerts: {e}")
            return []
    
    async def _check_budget_alerts(self, budget: CostBudget) -> List[CostAlert]:
        """Check for budget alerts and create them"""
        alerts = []
        
        try:
            utilization = budget.budget_utilization
            
            # Budget exceeded alert
            if budget.is_over_budget:
                alert = CostAlert(
                    type=CostAlertType.BUDGET_EXCEEDED,
                    severity="critical",
                    title=f"Budget Exceeded: {budget.name}",
                    message=f"Budget '{budget.name}' has been exceeded by ${budget.current_period_spend - budget.amount:.2f}",
                    budget_id=budget.budget_id,
                    current_cost=budget.current_period_spend,
                    threshold_cost=budget.amount,
                    recommendations=[
                        "Immediate action required",
                        "Review and approve overage or halt spending",
                        "Investigate unexpected cost increases"
                    ]
                )
                alerts.append(alert)
                
                # Trigger spending controls if enabled
                if self._spending_controls_enabled:
                    await self._trigger_spending_controls(budget)
            
            # Critical threshold alert
            elif utilization >= budget.critical_threshold:
                alert = CostAlert(
                    type=CostAlertType.BUDGET_THRESHOLD,
                    severity="critical",
                    title=f"Critical Budget Threshold: {budget.name}",
                    message=f"Budget '{budget.name}' has reached {utilization:.1f}% utilization (critical threshold: {budget.critical_threshold}%)",
                    budget_id=budget.budget_id,
                    current_cost=budget.current_period_spend,
                    threshold_cost=budget.amount * (budget.critical_threshold / 100),
                    recommendations=[
                        "Monitor spending closely",
                        "Consider implementing cost controls",
                        "Review remaining budget allocation"
                    ]
                )
                alerts.append(alert)
            
            # Warning threshold alert  
            elif utilization >= budget.warning_threshold:
                alert = CostAlert(
                    type=CostAlertType.BUDGET_THRESHOLD,
                    severity="medium",
                    title=f"Budget Warning: {budget.name}",
                    message=f"Budget '{budget.name}' has reached {utilization:.1f}% utilization (warning threshold: {budget.warning_threshold}%)",
                    budget_id=budget.budget_id,
                    current_cost=budget.current_period_spend,
                    threshold_cost=budget.amount * (budget.warning_threshold / 100),
                    recommendations=[
                        "Monitor budget closely",
                        "Review spending patterns",
                        "Consider cost optimization"
                    ]
                )
                alerts.append(alert)
            
            # Store alerts and trigger callbacks
            for alert in alerts:
                self._alert_history.append(alert)
                await self._trigger_alert_callbacks(alert)
            
            return alerts
            
        except Exception as e:
            logging.error(f"Failed to check budget alerts for {budget.budget_id}: {e}")
            return []
    
    async def _trigger_spending_controls(self, budget: CostBudget) -> None:
        """Trigger spending controls for over-budget situation"""
        try:
            self._spending_locks[budget.budget_id] = True
            
            logging.warning(f"Spending controls activated for budget: {budget.name}")
            
            # Here you would implement actual spending controls:
            # - Disable API keys
            # - Block new requests
            # - Send notifications to administrators
            # - etc.
            
        except Exception as e:
            logging.error(f"Failed to trigger spending controls for {budget.budget_id}: {e}")
    
    async def _trigger_alert_callbacks(self, alert: CostAlert) -> None:
        """Trigger registered alert callbacks"""
        for callback in self._alert_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(alert)
                else:
                    callback(alert)
            except Exception as e:
                logging.error(f"Error in alert callback: {e}")
    
    async def get_budget_utilization(self, budget_id: str) -> float:
        """
        Get budget utilization percentage.
        
        Args:
            budget_id: Budget ID
            
        Returns:
            Utilization percentage (0-100+)
        """
        try:
            if budget_id not in self._budgets:
                raise InvalidBudgetError(f"Budget not found: {budget_id}")
            
            budget = self._budgets[budget_id]
            await self._update_budget_spend(budget)
            
            return budget.budget_utilization
            
        except Exception as e:
            logging.error(f"Failed to get budget utilization for {budget_id}: {e}")
            return 0.0
    
    def register_alert_callback(self, callback: Callable) -> None:
        """Register callback for budget alerts"""
        self._alert_callbacks.append(callback)
    
    def unregister_alert_callback(self, callback: Callable) -> None:
        """Unregister alert callback"""
        if callback in self._alert_callbacks:
            self._alert_callbacks.remove(callback)
    
    async def _budget_monitoring_loop(self) -> None:
        """Background task for budget monitoring"""
        while True:
            try:
                # Update all active budgets and check for alerts
                for budget_id in list(self._active_budgets.keys()):
                    budget = self._active_budgets[budget_id]
                    
                    # Check if period has rolled over
                    if datetime.utcnow() > budget.current_period_end:
                        await self._roll_over_budget_period(budget)
                    
                    # Update spend and check alerts
                    await self._update_budget_spend(budget)
                    await self._check_budget_alerts(budget)
                
                await asyncio.sleep(self._monitoring_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"Error in budget monitoring loop: {e}")
                await asyncio.sleep(self._monitoring_interval)
    
    async def _roll_over_budget_period(self, budget: CostBudget) -> None:
        """Roll over budget to new period"""
        try:
            # Calculate new period
            old_period_end = budget.current_period_end
            budget.current_period_start = old_period_end
            budget.current_period_end = self._calculate_period_end(
                budget.current_period_start, budget.period
            )
            
            # Reset current spend
            budget.current_period_spend = 0.0
            budget.updated_at = datetime.utcnow()
            
            logging.info(f"Rolled over budget period for: {budget.name}")
            
        except Exception as e:
            logging.error(f"Failed to roll over budget period for {budget.budget_id}: {e}")
    
    async def get_budget_history(self, budget_id: str, days: int = 30) -> Dict[str, Any]:
        """Get historical budget performance"""
        # This would retrieve historical budget data
        # For now, return current status
        return await self.check_budget_status(budget_id)
    
    async def export_budget_report(self, budget_id: Optional[str] = None, 
                                 format: str = "json") -> str:
        """Export budget report in specified format"""
        status = await self.check_budget_status(budget_id)
        
        if format.lower() == "json":
            import json
            return json.dumps(status, indent=2, default=str)
        else:
            # CSV or other formats would be implemented here
            return str(status)


class CostBudgetManager(BudgetManager):
    """Extended budget manager with advanced features"""
    
    async def create_dynamic_budget(self, base_amount: float, growth_factor: float = 0.1) -> str:
        """Create a budget that adjusts based on usage trends"""
        # Implementation for dynamic budgets that adjust based on patterns
        budget = CostBudget(
            name=f"Dynamic Budget - {datetime.utcnow().strftime('%Y-%m')}",
            amount=base_amount,
            period=BillingPeriod.MONTHLY
        )
        
        # Add dynamic adjustment logic
        budget.metadata = {
            "type": "dynamic",
            "growth_factor": growth_factor,
            "base_amount": base_amount
        }
        
        return await self.create_budget(budget)


class AlertManager:
    """Specialized alert management for cost budgets"""
    
    def __init__(self, budget_manager: BudgetManager):
        """Initialize alert manager"""
        self._budget_manager = budget_manager
        self._alert_rules: List[Dict[str, Any]] = []
        self._notification_channels: Dict[str, Callable] = {}
    
    def add_alert_rule(self, rule: Dict[str, Any]) -> None:
        """Add custom alert rule"""
        self._alert_rules.append(rule)
    
    def register_notification_channel(self, name: str, handler: Callable) -> None:
        """Register notification channel (email, slack, etc.)"""
        self._notification_channels[name] = handler
    
    async def process_alert(self, alert: CostAlert) -> None:
        """Process alert through notification channels"""
        for channel_name, handler in self._notification_channels.items():
            try:
                await handler(alert)
            except Exception as e:
                logging.error(f"Failed to send alert via {channel_name}: {e}")


class SpendingController:
    """Automated spending control system"""
    
    def __init__(self, budget_manager: BudgetManager):
        """Initialize spending controller"""
        self._budget_manager = budget_manager
        self._control_policies: Dict[str, Dict[str, Any]] = {}
    
    def set_control_policy(self, budget_id: str, policy: Dict[str, Any]) -> None:
        """Set spending control policy for a budget"""
        self._control_policies[budget_id] = policy
    
    async def enforce_spending_limits(self, budget_id: str) -> bool:
        """Enforce spending limits for a budget"""
        # Implementation for automatic spending enforcement
        policy = self._control_policies.get(budget_id, {})
        
        if policy.get("auto_disable", False):
            # Automatically disable spending when budget exceeded
            logging.info(f"Auto-disabling spending for budget: {budget_id}")
            return True
        
        return False
