"""
LangSwarm V2 Cost Management System

Centralized cost management system that coordinates all cost-related
functionality including tracking, optimization, budgeting, billing, and recommendations.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta

from .interfaces import (
    CostEntry, CostSummary, CostBudget, CostAlert, CostForecast,
    BillingRecord, UsageRecord, CostRecommendation,
    BillingPeriod, CostManagementError
)

from .tracker import CostTracker, RealTimeCostTracker
from .optimizer import CostOptimizer, ProviderCostOptimizer
from .predictor import CostPredictor, UsageForecaster, BudgetPlanner
from .budget import BudgetManager, AlertManager, SpendingController
from .billing import BillingSystem, ChargebackSystem, InvoiceGenerator
from .recommendations import RecommendationEngine, CostOptimizationEngine


class CostManagementSystem:
    """
    Comprehensive cost management system.
    
    Integrates all cost management components into a unified system
    for tracking, optimizing, budgeting, billing, and recommending cost improvements.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize cost management system.
        
        Args:
            config: System configuration
        """
        self._config = config or {}
        
        # Initialize core components
        self._cost_tracker = self._create_cost_tracker()
        self._cost_optimizer = CostOptimizer(self._cost_tracker, self._config.get("optimizer", {}))
        self._cost_predictor = CostPredictor(self._cost_tracker, self._config.get("predictor", {}))
        self._budget_manager = BudgetManager(self._cost_tracker, self._config.get("budget", {}))
        self._billing_system = BillingSystem(self._cost_tracker, self._config.get("billing", {}))
        self._recommendation_engine = RecommendationEngine(
            self._cost_tracker, self._cost_optimizer, self._config.get("recommendations", {})
        )
        
        # Additional specialized components
        self._alert_manager = AlertManager(self._budget_manager)
        self._spending_controller = SpendingController(self._budget_manager)
        self._chargeback_system = ChargebackSystem(self._billing_system)
        self._invoice_generator = InvoiceGenerator(self._billing_system)
        
        # System state
        self._initialized = False
        self._monitoring_enabled = self._config.get("monitoring_enabled", True)
        self._auto_optimization_enabled = self._config.get("auto_optimization_enabled", False)
        
        # Background tasks
        self._monitoring_tasks: List[asyncio.Task] = []
        
        logging.info("Initialized Cost Management System")
    
    def _create_cost_tracker(self) -> CostTracker:
        """Create appropriate cost tracker based on configuration"""
        tracker_config = self._config.get("tracker", {})
        tracker_type = tracker_config.get("type", "standard")
        
        if tracker_type == "realtime":
            return RealTimeCostTracker(**tracker_config)
        else:
            return CostTracker(**tracker_config)
    
    async def initialize(self) -> None:
        """Initialize the cost management system"""
        if self._initialized:
            return
        
        try:
            # Initialize components
            await self._budget_manager.initialize()
            
            # Set up alert callbacks
            self._budget_manager.register_alert_callback(self._handle_cost_alert)
            
            # Start monitoring if enabled
            if self._monitoring_enabled:
                await self._start_monitoring()
            
            self._initialized = True
            logging.info("Cost Management System initialization complete")
            
        except Exception as e:
            logging.error(f"Failed to initialize Cost Management System: {e}")
            raise CostManagementError(f"System initialization failed: {e}")
    
    async def shutdown(self) -> None:
        """Shutdown the cost management system"""
        logging.info("Shutting down Cost Management System")
        
        # Cancel monitoring tasks
        for task in self._monitoring_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        # Shutdown components
        await self._budget_manager.shutdown()
        
        self._initialized = False
        logging.info("Cost Management System shutdown complete")
    
    async def _start_monitoring(self) -> None:
        """Start background monitoring tasks"""
        # Start optimization monitoring if enabled
        if self._auto_optimization_enabled:
            optimization_task = asyncio.create_task(self._optimization_monitoring_loop())
            self._monitoring_tasks.append(optimization_task)
        
        # Start cost anomaly detection
        anomaly_task = asyncio.create_task(self._anomaly_detection_loop())
        self._monitoring_tasks.append(anomaly_task)
        
        # Start periodic reporting
        reporting_task = asyncio.create_task(self._periodic_reporting_loop())
        self._monitoring_tasks.append(reporting_task)
    
    async def _handle_cost_alert(self, alert: CostAlert) -> None:
        """Handle cost alerts from budget manager"""
        try:
            logging.warning(f"Cost alert: {alert.title} - {alert.message}")
            
            # Auto-trigger spending controls if critical
            if alert.severity == "critical" and alert.type.value == "budget_exceeded":
                await self._spending_controller.enforce_spending_limits(alert.budget_id)
            
            # Generate immediate recommendations for cost issues
            if alert.type.value in ["budget_threshold", "budget_exceeded"]:
                recommendations = await self._recommendation_engine.generate_recommendations()
                high_priority_recs = [r for r in recommendations if r.priority == "high"]
                
                if high_priority_recs:
                    logging.info(f"Generated {len(high_priority_recs)} high-priority cost recommendations")
        
        except Exception as e:
            logging.error(f"Error handling cost alert: {e}")
    
    # Cost Tracking Interface
    async def track_cost(self, provider: str, model: str, usage: Dict[str, Any], cost: float, **kwargs) -> None:
        """
        Track a cost entry.
        
        Args:
            provider: Provider name
            model: Model name
            usage: Usage details (tokens, requests, etc.)
            cost: Cost amount
            **kwargs: Additional metadata
        """
        try:
            # Create cost entry
            cost_entry = CostEntry(
                provider=provider,
                model=model,
                amount=cost,
                input_tokens=usage.get("input_tokens", 0),
                output_tokens=usage.get("output_tokens", 0),
                total_tokens=usage.get("total_tokens", 0),
                requests=usage.get("requests", 1),
                user_id=kwargs.get("user_id"),
                session_id=kwargs.get("session_id"),
                project_id=kwargs.get("project_id"),
                department=kwargs.get("department"),
                metadata=kwargs.get("metadata", {}),
                tags=kwargs.get("tags", [])
            )
            
            # Track cost
            await self._cost_tracker.track_cost(cost_entry)
            
            # Track usage for billing
            usage_record = UsageRecord(
                user_id=kwargs.get("user_id", ""),
                session_id=kwargs.get("session_id"),
                project_id=kwargs.get("project_id"),
                department=kwargs.get("department"),
                provider=provider,
                model=model,
                input_tokens=usage.get("input_tokens", 0),
                output_tokens=usage.get("output_tokens", 0),
                total_tokens=usage.get("total_tokens", 0),
                requests=usage.get("requests", 1),
                cost=cost,
                metadata=kwargs.get("metadata", {})
            )
            
            await self._billing_system.track_usage(usage_record)
            
        except Exception as e:
            logging.error(f"Failed to track cost: {e}")
            raise CostManagementError(f"Cost tracking failed: {e}")
    
    async def get_cost_summary(self, provider: str = None, period: str = "day") -> Dict[str, Any]:
        """
        Get cost summary for a period.
        
        Args:
            provider: Optional provider filter
            period: Period type ("hour", "day", "week", "month")
            
        Returns:
            Cost summary data
        """
        try:
            # Calculate period dates
            end_date = datetime.utcnow()
            
            if period == "hour":
                start_date = end_date - timedelta(hours=1)
            elif period == "day":
                start_date = end_date - timedelta(days=1)
            elif period == "week":
                start_date = end_date - timedelta(days=7)
            elif period == "month":
                start_date = end_date - timedelta(days=30)
            else:
                start_date = end_date - timedelta(days=1)  # Default to day
            
            # Get cost summary
            summary = await self._cost_tracker.get_cost_summary(provider, start_date, end_date)
            
            # Convert to dictionary format
            return {
                "period": period,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "total_cost": summary.total_cost,
                "total_requests": summary.total_requests,
                "total_tokens": summary.total_tokens,
                "average_cost_per_request": summary.average_cost_per_request,
                "average_cost_per_token": summary.average_cost_per_token,
                "provider_costs": summary.provider_costs,
                "model_costs": summary.model_costs,
                "category_costs": {cat.value: cost for cat, cost in summary.category_costs.items()},
                "most_expensive_provider": summary.most_expensive_provider,
                "most_expensive_model": summary.most_expensive_model,
                "cost_trend": summary.cost_trend,
                "usage_trend": summary.usage_trend
            }
            
        except Exception as e:
            logging.error(f"Failed to get cost summary: {e}")
            return {"error": str(e)}
    
    # Optimization Interface
    async def optimize_costs(self, provider: str = None) -> Dict[str, Any]:
        """
        Run cost optimization analysis.
        
        Args:
            provider: Optional provider to focus on
            
        Returns:
            Optimization analysis and recommendations
        """
        try:
            # Run cost analysis
            analysis = await self._cost_optimizer.analyze_costs(provider)
            
            # Generate recommendations
            recommendations = await self._recommendation_engine.generate_recommendations(provider)
            
            # Calculate total potential savings
            total_savings = await self._cost_optimizer.calculate_potential_savings(recommendations)
            
            return {
                "analysis": analysis,
                "recommendations": [
                    {
                        "id": rec.recommendation_id,
                        "type": rec.type,
                        "priority": rec.priority,
                        "title": rec.title,
                        "description": rec.description,
                        "potential_savings": rec.potential_savings,
                        "savings_percentage": rec.savings_percentage,
                        "implementation_effort": rec.implementation_effort,
                        "actions": rec.recommended_actions
                    }
                    for rec in recommendations
                ],
                "total_potential_savings": total_savings,
                "optimization_score": self._calculate_optimization_score(analysis, recommendations),
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logging.error(f"Failed to optimize costs: {e}")
            return {"error": str(e)}
    
    def _calculate_optimization_score(self, analysis: Dict[str, Any], recommendations: List[CostRecommendation]) -> float:
        """Calculate overall optimization score (0-100)"""
        if not recommendations:
            return 100.0  # No recommendations means already optimized
        
        # Base score on cost efficiency
        total_cost = analysis.get("total_cost", 0)
        if total_cost == 0:
            return 100.0
        
        # Calculate potential improvement
        total_savings = sum(rec.potential_savings for rec in recommendations)
        improvement_potential = (total_savings / total_cost) * 100 if total_cost > 0 else 0
        
        # Score is inverse of improvement potential (less potential = higher score)
        optimization_score = max(0, 100 - improvement_potential)
        
        return optimization_score
    
    async def get_recommendations(self, provider: str = None) -> List[Dict[str, Any]]:
        """
        Get cost optimization recommendations.
        
        Args:
            provider: Optional provider filter
            
        Returns:
            List of recommendations
        """
        try:
            recommendations = await self._recommendation_engine.generate_recommendations(provider)
            
            return [
                {
                    "id": rec.recommendation_id,
                    "type": rec.type,
                    "priority": rec.priority,
                    "title": rec.title,
                    "description": rec.description,
                    "rationale": rec.rationale,
                    "potential_savings": rec.potential_savings,
                    "savings_percentage": rec.savings_percentage,
                    "implementation_effort": rec.implementation_effort,
                    "provider": rec.provider,
                    "model": rec.model,
                    "actions": rec.recommended_actions,
                    "status": rec.status,
                    "created_at": rec.created_at.isoformat(),
                    "metadata": rec.metadata
                }
                for rec in recommendations
            ]
            
        except Exception as e:
            logging.error(f"Failed to get recommendations: {e}")
            return []
    
    # Budget Management Interface
    async def create_budget(self, name: str, amount: float, period: str = "monthly", **kwargs) -> str:
        """
        Create a cost budget.
        
        Args:
            name: Budget name
            amount: Budget amount
            period: Billing period
            **kwargs: Additional budget configuration
            
        Returns:
            Budget ID
        """
        try:
            # Convert period string to enum
            period_enum = BillingPeriod(period.lower())
            
            # Create budget configuration
            budget = CostBudget(
                name=name,
                amount=amount,
                period=period_enum,
                providers=kwargs.get("providers", []),
                models=kwargs.get("models", []),
                user_ids=kwargs.get("user_ids", []),
                project_ids=kwargs.get("project_ids", []),
                departments=kwargs.get("departments", []),
                warning_threshold=kwargs.get("warning_threshold", 80.0),
                critical_threshold=kwargs.get("critical_threshold", 95.0),
                active=kwargs.get("active", True)
            )
            
            # Create budget
            budget_id = await self._budget_manager.create_budget(budget)
            
            logging.info(f"Created budget: {name} (${amount}) - {budget_id}")
            return budget_id
            
        except Exception as e:
            logging.error(f"Failed to create budget: {e}")
            raise CostManagementError(f"Budget creation failed: {e}")
    
    async def check_budget_status(self) -> Dict[str, Any]:
        """Check current budget status"""
        try:
            return await self._budget_manager.check_budget_status()
        except Exception as e:
            logging.error(f"Failed to check budget status: {e}")
            return {"error": str(e)}
    
    # Billing Interface
    async def generate_bill(self, customer_id: str, period: str = "monthly") -> Dict[str, Any]:
        """
        Generate a bill for a customer.
        
        Args:
            customer_id: Customer identifier
            period: Billing period
            
        Returns:
            Billing information
        """
        try:
            # Convert period to enum
            period_enum = BillingPeriod(period.lower())
            
            # Calculate period dates
            end_date = datetime.utcnow()
            if period == "monthly":
                start_date = end_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            elif period == "weekly":
                days_since_monday = end_date.weekday()
                start_date = end_date - timedelta(days=days_since_monday)
                start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            else:
                start_date = end_date - timedelta(days=30)  # Default
            
            # Generate bill
            billing_record = await self._billing_system.generate_bill(
                customer_id, period_enum, start_date, end_date
            )
            
            # Generate invoice
            invoice = await self._billing_system.generate_invoice(billing_record.record_id)
            
            return {
                "billing_record_id": billing_record.record_id,
                "customer_id": customer_id,
                "period": period,
                "amount": billing_record.total_amount,
                "currency": billing_record.currency,
                "line_items": billing_record.line_items,
                "invoice": invoice
            }
            
        except Exception as e:
            logging.error(f"Failed to generate bill for {customer_id}: {e}")
            return {"error": str(e)}
    
    async def calculate_chargeback(self, department: str, period: str = "monthly") -> Dict[str, Any]:
        """
        Calculate chargeback for a department.
        
        Args:
            department: Department name
            period: Billing period
            
        Returns:
            Chargeback calculation
        """
        try:
            period_enum = BillingPeriod(period.lower())
            return await self._billing_system.calculate_chargeback(department, period_enum)
        except Exception as e:
            logging.error(f"Failed to calculate chargeback for {department}: {e}")
            return {"error": str(e)}
    
    # Prediction Interface
    async def predict_costs(self, provider: str = None, days: int = 30) -> Dict[str, Any]:
        """
        Predict future costs.
        
        Args:
            provider: Optional provider filter
            days: Number of days to predict
            
        Returns:
            Cost forecast
        """
        try:
            if provider:
                forecast = await self._cost_predictor.predict_costs(provider, days)
            else:
                # Predict for all providers and aggregate
                cost_summary = await self._cost_tracker.get_cost_summary()
                forecasts = []
                
                for prov in cost_summary.provider_costs.keys():
                    prov_forecast = await self._cost_predictor.predict_costs(prov, days)
                    forecasts.append(prov_forecast)
                
                # Create aggregate forecast
                total_predicted = sum(f.predicted_cost for f in forecasts)
                total_lower = sum(f.lower_bound for f in forecasts)
                total_upper = sum(f.upper_bound for f in forecasts)
                
                forecast = CostForecast(
                    provider="all",
                    period_start=datetime.utcnow(),
                    period_end=datetime.utcnow() + timedelta(days=days),
                    predicted_cost=total_predicted,
                    lower_bound=total_lower,
                    upper_bound=total_upper,
                    confidence_level=0.8
                )
            
            return {
                "provider": forecast.provider,
                "forecast_period": {
                    "start": forecast.period_start.isoformat(),
                    "end": forecast.period_end.isoformat(),
                    "days": days
                },
                "predicted_cost": forecast.predicted_cost,
                "confidence_level": forecast.confidence_level,
                "lower_bound": forecast.lower_bound,
                "upper_bound": forecast.upper_bound,
                "trend_direction": forecast.trend_direction,
                "methodology": forecast.methodology,
                "data_quality": forecast.data_quality,
                "assumptions": forecast.assumptions
            }
            
        except Exception as e:
            logging.error(f"Failed to predict costs: {e}")
            return {"error": str(e)}
    
    # Monitoring Loops
    async def _optimization_monitoring_loop(self) -> None:
        """Background task for automatic optimization monitoring"""
        while True:
            try:
                # Run optimization analysis every hour
                recommendations = await self._recommendation_engine.generate_recommendations()
                
                # Auto-apply low-risk, high-savings recommendations
                for rec in recommendations:
                    if (rec.priority == "high" and 
                        rec.implementation_effort == "low" and 
                        rec.potential_savings > 100):
                        
                        logging.info(f"Auto-optimization opportunity detected: {rec.title}")
                        # Here you would implement auto-application logic
                
                await asyncio.sleep(3600)  # 1 hour
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"Error in optimization monitoring: {e}")
                await asyncio.sleep(3600)
    
    async def _anomaly_detection_loop(self) -> None:
        """Background task for cost anomaly detection"""
        while True:
            try:
                # Check for unusual spending patterns every 15 minutes
                stats = await self._cost_tracker.get_realtime_stats()
                
                # Simple anomaly detection
                current_hour_cost = stats.get("total_cost", 0)
                if current_hour_cost > 1000:  # High hourly cost threshold
                    logging.warning(f"High cost anomaly detected: ${current_hour_cost:.2f} in current period")
                
                await asyncio.sleep(900)  # 15 minutes
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"Error in anomaly detection: {e}")
                await asyncio.sleep(900)
    
    async def _periodic_reporting_loop(self) -> None:
        """Background task for periodic reporting"""
        while True:
            try:
                # Generate daily reports
                summary = await self.get_cost_summary(period="day")
                recommendations = await self.get_recommendations()
                
                logging.info(f"Daily cost summary: ${summary.get('total_cost', 0):.2f}")
                logging.info(f"Active recommendations: {len(recommendations)}")
                
                await asyncio.sleep(86400)  # 24 hours
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"Error in periodic reporting: {e}")
                await asyncio.sleep(86400)
    
    # Utility Methods
    async def get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data"""
        try:
            # Gather data from all components
            cost_summary = await self.get_cost_summary(period="day")
            budget_status = await self.check_budget_status()
            recommendations = await self.get_recommendations()
            cost_forecast = await self.predict_costs(days=7)
            
            return {
                "cost_summary": cost_summary,
                "budget_status": budget_status,
                "recommendations": {
                    "total": len(recommendations),
                    "high_priority": len([r for r in recommendations if r["priority"] == "high"]),
                    "potential_savings": sum(r["potential_savings"] for r in recommendations),
                    "top_recommendations": recommendations[:5]
                },
                "forecast": cost_forecast,
                "alerts": {
                    "active_count": len([a for a in self._alert_manager._alert_history if not a.acknowledged]),
                    "critical_count": len([a for a in self._alert_manager._alert_history if a.severity == "critical" and not a.acknowledged])
                },
                "system_health": {
                    "tracking": "operational",
                    "budgeting": "operational", 
                    "optimization": "operational",
                    "billing": "operational"
                },
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logging.error(f"Failed to get dashboard data: {e}")
            return {"error": str(e)}


class GlobalCostManager(CostManagementSystem):
    """Global singleton cost manager for system-wide cost management"""
    
    _instance: Optional['GlobalCostManager'] = None
    
    def __new__(cls, config: Dict[str, Any] = None):
        """Ensure singleton instance"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize only once"""
        if not hasattr(self, '_initialized_singleton'):
            super().__init__(config)
            self._initialized_singleton = True


# Factory function for creating cost management systems
def create_cost_management_system(config: Dict[str, Any] = None) -> CostManagementSystem:
    """
    Create a cost management system instance.
    
    Args:
        config: System configuration
        
    Returns:
        Cost management system instance
    """
    return CostManagementSystem(config)
