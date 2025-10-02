"""
LangSwarm V2 Cost Predictor

Sophisticated cost prediction and forecasting system with capacity planning,
budget burn analysis, and usage trend prediction capabilities.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import statistics
import math

from .interfaces import (
    ICostPredictor, CostForecast, CostBudget, CostEntry,
    ForecastingError
)


class CostPredictor(ICostPredictor):
    """
    Comprehensive cost prediction and forecasting system.
    
    Provides sophisticated forecasting capabilities using multiple algorithms
    including linear regression, seasonal analysis, and machine learning models.
    """
    
    def __init__(self, cost_tracker, config: Dict[str, Any] = None):
        """
        Initialize cost predictor.
        
        Args:
            cost_tracker: Cost tracking system instance
            config: Prediction configuration
        """
        self._cost_tracker = cost_tracker
        self._config = config or {}
        
        # Forecasting parameters
        self._forecasting_params = {
            "min_historical_days": 7,     # Minimum days needed for prediction
            "max_historical_days": 90,    # Maximum days to consider
            "confidence_levels": [0.5, 0.8, 0.9, 0.95],
            "seasonality_detection_threshold": 0.3,
            "trend_detection_threshold": 0.1
        }
        
        # Forecasting methods available
        self._forecasting_methods = [
            "linear_regression",
            "moving_average", 
            "exponential_smoothing",
            "seasonal_decomposition",
            "trend_analysis"
        ]
        
        logging.info("Initialized Cost Predictor")
    
    async def predict_costs(self, provider: str, 
                          forecast_days: int = 30,
                          confidence_level: float = 0.8) -> CostForecast:
        """
        Predict future costs based on historical data.
        
        Args:
            provider: Provider to predict costs for
            forecast_days: Number of days to forecast
            confidence_level: Confidence level for prediction (0.0-1.0)
            
        Returns:
            Cost forecast with prediction bounds
        """
        try:
            # Get historical data
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=min(90, forecast_days * 3))  # 3x forecast period
            
            historical_summary = await self._cost_tracker.get_cost_summary(
                provider, start_date, end_date
            )
            
            if historical_summary.total_cost == 0:
                return CostForecast(
                    provider=provider,
                    period_start=end_date,
                    period_end=end_date + timedelta(days=forecast_days),
                    predicted_cost=0.0,
                    confidence_level=confidence_level,
                    lower_bound=0.0,
                    upper_bound=0.0,
                    data_quality="poor",
                    methodology="insufficient_data"
                )
            
            # Get daily cost data for analysis
            daily_costs = await self._get_daily_costs(provider, start_date, end_date)
            
            if len(daily_costs) < self._forecasting_params["min_historical_days"]:
                raise ForecastingError(f"Insufficient historical data: {len(daily_costs)} days available, minimum {self._forecasting_params['min_historical_days']} required")
            
            # Analyze data quality
            data_quality = self._assess_data_quality(daily_costs)
            
            # Select best forecasting method
            methodology = self._select_forecasting_method(daily_costs)
            
            # Generate forecast
            prediction_result = await self._generate_forecast(
                daily_costs, forecast_days, methodology, confidence_level
            )
            
            # Create forecast object
            forecast = CostForecast(
                provider=provider,
                period_start=end_date,
                period_end=end_date + timedelta(days=forecast_days),
                predicted_cost=prediction_result["predicted_cost"],
                confidence_level=confidence_level,
                lower_bound=prediction_result["lower_bound"],
                upper_bound=prediction_result["upper_bound"],
                historical_periods=len(daily_costs),
                data_quality=data_quality,
                trend_direction=prediction_result["trend_direction"],
                seasonality_detected=prediction_result["seasonality_detected"],
                methodology=methodology,
                assumptions=prediction_result["assumptions"],
                metadata=prediction_result["metadata"]
            )
            
            return forecast
            
        except Exception as e:
            logging.error(f"Cost prediction failed for {provider}: {e}")
            raise ForecastingError(f"Cost prediction failed: {e}")
    
    async def _get_daily_costs(self, provider: str, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get daily aggregated cost data"""
        daily_costs = []
        
        current_date = start_date
        while current_date <= end_date:
            day_end = current_date + timedelta(days=1)
            
            day_summary = await self._cost_tracker.get_cost_summary(
                provider, current_date, day_end
            )
            
            daily_costs.append({
                "date": current_date,
                "cost": day_summary.total_cost,
                "requests": day_summary.total_requests,
                "tokens": day_summary.total_tokens
            })
            
            current_date += timedelta(days=1)
        
        return daily_costs
    
    def _assess_data_quality(self, daily_costs: List[Dict[str, Any]]) -> str:
        """Assess the quality of historical data"""
        if not daily_costs:
            return "poor"
        
        # Calculate data consistency metrics
        costs = [day["cost"] for day in daily_costs]
        non_zero_days = len([c for c in costs if c > 0])
        total_days = len(costs)
        
        # Data coverage
        coverage = non_zero_days / total_days if total_days > 0 else 0
        
        # Variance analysis
        if len(costs) > 1:
            cost_variance = statistics.variance(costs) if len(costs) > 1 else 0
            mean_cost = statistics.mean(costs)
            coefficient_of_variation = (cost_variance ** 0.5) / mean_cost if mean_cost > 0 else float('inf')
        else:
            coefficient_of_variation = 0
        
        # Quality assessment
        if coverage >= 0.8 and coefficient_of_variation < 2.0:
            return "excellent"
        elif coverage >= 0.6 and coefficient_of_variation < 3.0:
            return "good"
        elif coverage >= 0.4 and coefficient_of_variation < 5.0:
            return "fair"
        else:
            return "poor"
    
    def _select_forecasting_method(self, daily_costs: List[Dict[str, Any]]) -> str:
        """Select the best forecasting method based on data characteristics"""
        if len(daily_costs) < 14:
            return "moving_average"
        elif len(daily_costs) < 30:
            return "linear_regression"
        else:
            # For longer series, check for seasonality and trends
            costs = [day["cost"] for day in daily_costs]
            
            # Simple seasonality detection (weekly patterns)
            if len(costs) >= 14:
                weekly_correlation = self._detect_weekly_seasonality(costs)
                if weekly_correlation > self._forecasting_params["seasonality_detection_threshold"]:
                    return "seasonal_decomposition"
            
            # Trend detection
            trend_strength = self._detect_trend(costs)
            if abs(trend_strength) > self._forecasting_params["trend_detection_threshold"]:
                return "trend_analysis"
            
            return "exponential_smoothing"
    
    def _detect_weekly_seasonality(self, costs: List[float]) -> float:
        """Detect weekly seasonality patterns"""
        if len(costs) < 14:
            return 0.0
        
        # Compare similar days of week
        weekly_patterns = []
        for day_offset in range(7):
            day_costs = [costs[i] for i in range(day_offset, len(costs), 7)]
            if len(day_costs) > 1:
                weekly_patterns.append(statistics.mean(day_costs))
        
        if len(weekly_patterns) >= 7:
            # Calculate variance in weekly patterns
            pattern_variance = statistics.variance(weekly_patterns)
            overall_variance = statistics.variance(costs)
            
            # Higher pattern variance relative to overall variance indicates seasonality
            return pattern_variance / overall_variance if overall_variance > 0 else 0.0
        
        return 0.0
    
    def _detect_trend(self, costs: List[float]) -> float:
        """Detect linear trend in costs"""
        if len(costs) < 3:
            return 0.0
        
        # Simple linear regression slope calculation
        n = len(costs)
        x_values = list(range(n))
        
        sum_x = sum(x_values)
        sum_y = sum(costs)
        sum_xy = sum(x * y for x, y in zip(x_values, costs))
        sum_x2 = sum(x * x for x in x_values)
        
        # Slope calculation
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        
        # Normalize slope by mean cost to get relative trend
        mean_cost = sum_y / n if n > 0 else 0
        normalized_slope = slope / mean_cost if mean_cost > 0 else 0
        
        return normalized_slope
    
    async def _generate_forecast(self, daily_costs: List[Dict[str, Any]], 
                               forecast_days: int, methodology: str, 
                               confidence_level: float) -> Dict[str, Any]:
        """Generate forecast using specified methodology"""
        costs = [day["cost"] for day in daily_costs]
        
        if methodology == "linear_regression":
            return self._linear_regression_forecast(costs, forecast_days, confidence_level)
        elif methodology == "moving_average":
            return self._moving_average_forecast(costs, forecast_days, confidence_level)
        elif methodology == "exponential_smoothing":
            return self._exponential_smoothing_forecast(costs, forecast_days, confidence_level)
        elif methodology == "seasonal_decomposition":
            return self._seasonal_forecast(costs, forecast_days, confidence_level)
        elif methodology == "trend_analysis":
            return self._trend_analysis_forecast(costs, forecast_days, confidence_level)
        else:
            # Default to moving average
            return self._moving_average_forecast(costs, forecast_days, confidence_level)
    
    def _linear_regression_forecast(self, costs: List[float], forecast_days: int, confidence_level: float) -> Dict[str, Any]:
        """Linear regression forecasting"""
        if len(costs) < 2:
            daily_avg = costs[0] if costs else 0.0
            predicted_cost = daily_avg * forecast_days
            return {
                "predicted_cost": predicted_cost,
                "lower_bound": predicted_cost * 0.8,
                "upper_bound": predicted_cost * 1.2,
                "trend_direction": "stable",
                "seasonality_detected": False,
                "assumptions": ["Insufficient data for trend analysis"],
                "metadata": {"method": "average_extrapolation"}
            }
        
        # Calculate linear regression
        n = len(costs)
        x_values = list(range(n))
        
        # Calculate slope and intercept
        sum_x = sum(x_values)
        sum_y = sum(costs)
        sum_xy = sum(x * y for x, y in zip(x_values, costs))
        sum_x2 = sum(x * x for x in x_values)
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        intercept = (sum_y - slope * sum_x) / n
        
        # Calculate R-squared for confidence assessment
        y_mean = sum_y / n
        ss_tot = sum((y - y_mean) ** 2 for y in costs)
        ss_res = sum((costs[i] - (slope * x_values[i] + intercept)) ** 2 for i in range(n))
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        
        # Predict future costs
        predicted_daily_costs = []
        for day in range(forecast_days):
            future_x = n + day
            predicted_daily = slope * future_x + intercept
            predicted_daily_costs.append(max(0, predicted_daily))  # Ensure non-negative
        
        predicted_cost = sum(predicted_daily_costs)
        
        # Calculate confidence bounds
        confidence_factor = 1.0 + (1.0 - confidence_level) * (1.0 - r_squared)
        margin = predicted_cost * confidence_factor * 0.3  # 30% base margin
        
        # Determine trend direction
        trend_direction = "increasing" if slope > 0.01 else "decreasing" if slope < -0.01 else "stable"
        
        return {
            "predicted_cost": predicted_cost,
            "lower_bound": max(0, predicted_cost - margin),
            "upper_bound": predicted_cost + margin,
            "trend_direction": trend_direction,
            "seasonality_detected": False,
            "assumptions": [
                "Linear trend continues",
                f"Historical R-squared: {r_squared:.3f}",
                "No major usage pattern changes"
            ],
            "metadata": {
                "method": "linear_regression",
                "slope": slope,
                "intercept": intercept,
                "r_squared": r_squared,
                "confidence_factor": confidence_factor
            }
        }
    
    def _moving_average_forecast(self, costs: List[float], forecast_days: int, confidence_level: float) -> Dict[str, Any]:
        """Moving average forecasting"""
        window_size = min(7, len(costs))  # 7-day moving average or all available data
        
        if len(costs) >= window_size:
            recent_costs = costs[-window_size:]
            daily_avg = statistics.mean(recent_costs)
            daily_variance = statistics.variance(recent_costs) if len(recent_costs) > 1 else 0
        else:
            daily_avg = statistics.mean(costs) if costs else 0
            daily_variance = statistics.variance(costs) if len(costs) > 1 else 0
        
        predicted_cost = daily_avg * forecast_days
        
        # Calculate confidence bounds based on historical variance
        std_dev = daily_variance ** 0.5
        confidence_multiplier = 2.0 if confidence_level >= 0.95 else 1.65 if confidence_level >= 0.9 else 1.28
        margin = std_dev * confidence_multiplier * (forecast_days ** 0.5)  # Adjust for forecast period
        
        return {
            "predicted_cost": predicted_cost,
            "lower_bound": max(0, predicted_cost - margin),
            "upper_bound": predicted_cost + margin,
            "trend_direction": "stable",
            "seasonality_detected": False,
            "assumptions": [
                f"Recent {window_size}-day average continues",
                "No significant trend or seasonality",
                "Historical variance patterns persist"
            ],
            "metadata": {
                "method": "moving_average",
                "window_size": window_size,
                "daily_average": daily_avg,
                "daily_variance": daily_variance
            }
        }
    
    def _exponential_smoothing_forecast(self, costs: List[float], forecast_days: int, confidence_level: float) -> Dict[str, Any]:
        """Exponential smoothing forecasting"""
        if not costs:
            return self._moving_average_forecast(costs, forecast_days, confidence_level)
        
        # Simple exponential smoothing
        alpha = 0.3  # Smoothing parameter
        smoothed_values = [costs[0]]
        
        for i in range(1, len(costs)):
            smoothed = alpha * costs[i] + (1 - alpha) * smoothed_values[-1]
            smoothed_values.append(smoothed)
        
        # Use last smoothed value for prediction
        last_smoothed = smoothed_values[-1]
        predicted_cost = last_smoothed * forecast_days
        
        # Calculate prediction intervals based on residuals
        residuals = [costs[i] - smoothed_values[i] for i in range(len(costs))]
        residual_std = statistics.stdev(residuals) if len(residuals) > 1 else 0
        
        confidence_multiplier = 2.0 if confidence_level >= 0.95 else 1.65 if confidence_level >= 0.9 else 1.28
        margin = residual_std * confidence_multiplier * (forecast_days ** 0.5)
        
        return {
            "predicted_cost": predicted_cost,
            "lower_bound": max(0, predicted_cost - margin),
            "upper_bound": predicted_cost + margin,
            "trend_direction": "stable",
            "seasonality_detected": False,
            "assumptions": [
                "Exponential smoothing pattern continues",
                f"Alpha smoothing parameter: {alpha}",
                "Recent observations weighted more heavily"
            ],
            "metadata": {
                "method": "exponential_smoothing",
                "alpha": alpha,
                "last_smoothed": last_smoothed,
                "residual_std": residual_std
            }
        }
    
    def _seasonal_forecast(self, costs: List[float], forecast_days: int, confidence_level: float) -> Dict[str, Any]:
        """Seasonal decomposition forecasting"""
        # Simplified seasonal forecasting (weekly patterns)
        if len(costs) < 14:
            return self._moving_average_forecast(costs, forecast_days, confidence_level)
        
        # Calculate weekly averages
        weekly_pattern = []
        for day_of_week in range(7):
            day_costs = [costs[i] for i in range(day_of_week, len(costs), 7)]
            if day_costs:
                weekly_pattern.append(statistics.mean(day_costs))
            else:
                weekly_pattern.append(0)
        
        # Overall trend (simplified)
        trend = (costs[-1] - costs[0]) / len(costs) if len(costs) > 1 else 0
        
        # Predict future costs using seasonal pattern + trend
        predicted_daily_costs = []
        for day in range(forecast_days):
            day_of_week = (len(costs) + day) % 7
            seasonal_component = weekly_pattern[day_of_week]
            trend_component = trend * (len(costs) + day)
            predicted_daily = seasonal_component + trend_component
            predicted_daily_costs.append(max(0, predicted_daily))
        
        predicted_cost = sum(predicted_daily_costs)
        
        # Calculate confidence bounds
        weekly_variance = statistics.variance(weekly_pattern) if len(weekly_pattern) > 1 else 0
        margin = (weekly_variance ** 0.5) * 1.5 * forecast_days
        
        return {
            "predicted_cost": predicted_cost,
            "lower_bound": max(0, predicted_cost - margin),
            "upper_bound": predicted_cost + margin,
            "trend_direction": "increasing" if trend > 0.01 else "decreasing" if trend < -0.01 else "stable",
            "seasonality_detected": True,
            "assumptions": [
                "Weekly seasonal pattern continues",
                "Linear trend component",
                "Pattern stability over forecast period"
            ],
            "metadata": {
                "method": "seasonal_decomposition",
                "weekly_pattern": weekly_pattern,
                "trend": trend,
                "weekly_variance": weekly_variance
            }
        }
    
    def _trend_analysis_forecast(self, costs: List[float], forecast_days: int, confidence_level: float) -> Dict[str, Any]:
        """Trend-based forecasting"""
        # Enhanced linear regression with trend analysis
        result = self._linear_regression_forecast(costs, forecast_days, confidence_level)
        
        # Adjust for accelerating/decelerating trends
        if len(costs) >= 6:
            # Compare recent trend to overall trend
            recent_trend = self._detect_trend(costs[-7:])  # Last week
            overall_trend = self._detect_trend(costs)
            
            trend_acceleration = recent_trend - overall_trend
            
            # Adjust prediction based on trend acceleration
            if abs(trend_acceleration) > 0.05:  # Significant acceleration
                adjustment_factor = 1.0 + trend_acceleration * forecast_days * 0.1
                result["predicted_cost"] *= adjustment_factor
                result["upper_bound"] *= adjustment_factor
                result["assumptions"].append(f"Trend acceleration factor: {adjustment_factor:.3f}")
        
        result["metadata"]["method"] = "trend_analysis"
        return result
    
    async def forecast_budget_burn(self, budget: CostBudget) -> Dict[str, Any]:
        """
        Forecast when budget will be exhausted.
        
        Args:
            budget: Budget to analyze
            
        Returns:
            Budget burn forecast with timeline
        """
        try:
            if budget.amount <= 0:
                return {"error": "Invalid budget amount"}
            
            # Get current spending for budget scope
            current_period_start = budget.current_period_start or datetime.utcnow().replace(day=1)
            current_date = datetime.utcnow()
            
            # Calculate current burn rate
            days_elapsed = (current_date - current_period_start).days + 1
            current_spend = budget.current_period_spend
            daily_burn_rate = current_spend / days_elapsed if days_elapsed > 0 else 0
            
            # Forecast based on providers in budget scope
            providers_to_forecast = budget.providers if budget.providers else ["all"]
            
            forecasts = []
            for provider in providers_to_forecast:
                if provider != "all":
                    forecast = await self.predict_costs(provider, 30)
                    forecasts.append(forecast)
            
            # Calculate projected burn rate
            if forecasts:
                total_predicted_monthly = sum(f.predicted_cost for f in forecasts)
                projected_daily_burn = total_predicted_monthly / 30
            else:
                # Use historical burn rate
                projected_daily_burn = daily_burn_rate
            
            # Calculate budget exhaustion timeline
            remaining_budget = budget.remaining_budget
            
            if projected_daily_burn <= 0:
                days_until_exhaustion = float('inf')
                exhaustion_date = None
            else:
                days_until_exhaustion = remaining_budget / projected_daily_burn
                exhaustion_date = current_date + timedelta(days=days_until_exhaustion)
            
            # Calculate budget period end
            if budget.period == budget.period.MONTHLY:
                period_end = (current_period_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            elif budget.period == budget.period.WEEKLY:
                period_end = current_period_start + timedelta(days=7)
            elif budget.period == budget.period.DAILY:
                period_end = current_period_start + timedelta(days=1)
            else:
                period_end = current_period_start + timedelta(days=30)  # Default to monthly
            
            # Determine budget status
            budget_status = "healthy"
            if budget.budget_utilization >= budget.critical_threshold:
                budget_status = "critical"
            elif budget.budget_utilization >= budget.warning_threshold:
                budget_status = "warning"
            
            return {
                "budget_id": budget.budget_id,
                "budget_name": budget.name,
                "budget_status": budget_status,
                "current_spend": current_spend,
                "remaining_budget": remaining_budget,
                "budget_utilization": budget.budget_utilization,
                "period_info": {
                    "start": current_period_start.isoformat(),
                    "end": period_end.isoformat(),
                    "days_elapsed": days_elapsed,
                    "days_remaining": (period_end - current_date).days
                },
                "burn_analysis": {
                    "current_daily_burn": daily_burn_rate,
                    "projected_daily_burn": projected_daily_burn,
                    "days_until_exhaustion": days_until_exhaustion if days_until_exhaustion != float('inf') else None,
                    "exhaustion_date": exhaustion_date.isoformat() if exhaustion_date else None,
                    "will_exceed_budget": exhaustion_date < period_end if exhaustion_date else False
                },
                "forecasts": [
                    {
                        "provider": f.provider,
                        "predicted_cost": f.predicted_cost,
                        "confidence": f.confidence_level
                    }
                    for f in forecasts
                ],
                "recommendations": self._generate_budget_recommendations(
                    budget, days_until_exhaustion, budget_status
                )
            }
            
        except Exception as e:
            logging.error(f"Budget burn forecast failed: {e}")
            raise ForecastingError(f"Budget burn forecast failed: {e}")
    
    def _generate_budget_recommendations(self, budget: CostBudget, 
                                       days_until_exhaustion: float, 
                                       status: str) -> List[str]:
        """Generate budget management recommendations"""
        recommendations = []
        
        if status == "critical":
            recommendations.append("Immediate action required: Budget will be exceeded soon")
            recommendations.append("Consider implementing cost controls or increasing budget")
        elif status == "warning":
            recommendations.append("Monitor spending closely - approaching budget threshold")
            recommendations.append("Review and optimize high-cost activities")
        
        if days_until_exhaustion < 7:
            recommendations.append("Budget exhaustion predicted within 7 days")
            recommendations.append("Consider pausing non-essential operations")
        elif days_until_exhaustion < 14:
            recommendations.append("Budget exhaustion predicted within 2 weeks")
            recommendations.append("Implement cost optimization measures")
        
        if not recommendations:
            recommendations.append("Budget is on track - continue monitoring")
        
        return recommendations
    
    async def predict_usage_trends(self, provider: Optional[str] = None) -> Dict[str, Any]:
        """
        Predict usage trends and patterns.
        
        Args:
            provider: Optional provider to focus analysis on
            
        Returns:
            Usage trend predictions and insights
        """
        try:
            # Get historical usage data
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=60)  # 60 days of history
            
            daily_costs = await self._get_daily_costs(provider or "all", start_date, end_date)
            
            if not daily_costs:
                return {"error": "No usage data available"}
            
            # Extract usage metrics
            costs = [day["cost"] for day in daily_costs]
            requests = [day["requests"] for day in daily_costs]
            tokens = [day["tokens"] for day in daily_costs]
            
            # Analyze trends
            cost_trend = self._detect_trend(costs)
            request_trend = self._detect_trend(requests)
            token_trend = self._detect_trend(tokens)
            
            # Detect patterns
            weekly_seasonality = self._detect_weekly_seasonality(costs)
            
            # Calculate growth rates
            if len(costs) >= 30:
                recent_avg = statistics.mean(costs[-7:])  # Last week
                older_avg = statistics.mean(costs[-30:-23])  # Week from 4 weeks ago
                week_over_week_growth = ((recent_avg - older_avg) / older_avg * 100) if older_avg > 0 else 0
            else:
                week_over_week_growth = 0
            
            # Predict future usage
            forecast_result = await self._generate_forecast(daily_costs, 30, "trend_analysis", 0.8)
            
            return {
                "provider": provider or "all",
                "analysis_period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                    "days": len(daily_costs)
                },
                "trends": {
                    "cost_trend": "increasing" if cost_trend > 0.05 else "decreasing" if cost_trend < -0.05 else "stable",
                    "request_trend": "increasing" if request_trend > 0.05 else "decreasing" if request_trend < -0.05 else "stable",
                    "token_trend": "increasing" if token_trend > 0.05 else "decreasing" if token_trend < -0.05 else "stable",
                    "cost_trend_strength": abs(cost_trend),
                    "request_trend_strength": abs(request_trend),
                    "token_trend_strength": abs(token_trend)
                },
                "patterns": {
                    "weekly_seasonality": weekly_seasonality > 0.3,
                    "seasonality_strength": weekly_seasonality
                },
                "growth_metrics": {
                    "week_over_week_growth": week_over_week_growth,
                    "projected_monthly_cost": forecast_result["predicted_cost"],
                    "growth_classification": (
                        "high_growth" if week_over_week_growth > 20 else
                        "moderate_growth" if week_over_week_growth > 5 else
                        "stable" if week_over_week_growth > -5 else
                        "declining"
                    )
                },
                "forecasts": {
                    "next_30_days": forecast_result,
                    "confidence": forecast_result.get("metadata", {}).get("r_squared", 0.5)
                },
                "insights": self._generate_usage_insights(cost_trend, week_over_week_growth, weekly_seasonality)
            }
            
        except Exception as e:
            logging.error(f"Usage trend prediction failed: {e}")
            raise ForecastingError(f"Usage trend prediction failed: {e}")
    
    def _generate_usage_insights(self, cost_trend: float, growth_rate: float, seasonality: float) -> List[str]:
        """Generate insights about usage trends"""
        insights = []
        
        if growth_rate > 50:
            insights.append("Rapid growth detected - consider capacity planning")
        elif growth_rate > 20:
            insights.append("High growth rate - monitor for budget impact")
        elif growth_rate < -20:
            insights.append("Declining usage - investigate potential issues")
        
        if abs(cost_trend) > 0.1:
            insights.append(f"Strong {'upward' if cost_trend > 0 else 'downward'} cost trend detected")
        
        if seasonality > 0.4:
            insights.append("Strong weekly patterns detected - consider optimizing for peak usage")
        
        if not insights:
            insights.append("Usage patterns appear stable and predictable")
        
        return insights
    
    async def capacity_planning(self, target_growth: float) -> Dict[str, Any]:
        """
        Perform capacity planning for cost budgeting.
        
        Args:
            target_growth: Expected growth rate (e.g., 0.5 for 50% growth)
            
        Returns:
            Capacity planning recommendations and cost projections
        """
        try:
            # Get current baseline
            current_summary = await self._cost_tracker.get_cost_summary()
            
            if current_summary.total_cost == 0:
                return {"error": "No baseline cost data available"}
            
            # Calculate projected costs
            current_monthly_cost = current_summary.total_cost
            projected_monthly_cost = current_monthly_cost * (1 + target_growth)
            additional_cost = projected_monthly_cost - current_monthly_cost
            
            # Provider-specific projections
            provider_projections = {}
            for provider, current_cost in current_summary.provider_costs.items():
                projected_provider_cost = current_cost * (1 + target_growth)
                provider_projections[provider] = {
                    "current_cost": current_cost,
                    "projected_cost": projected_provider_cost,
                    "additional_cost": projected_provider_cost - current_cost
                }
            
            # Calculate infrastructure requirements
            current_requests = current_summary.total_requests
            projected_requests = current_requests * (1 + target_growth)
            additional_requests = projected_requests - current_requests
            
            # Generate recommendations
            recommendations = []
            
            if target_growth > 1.0:  # > 100% growth
                recommendations.append("Consider negotiating volume discounts with providers")
                recommendations.append("Implement aggressive cost optimization measures")
                recommendations.append("Evaluate dedicated infrastructure options")
            elif target_growth > 0.5:  # > 50% growth
                recommendations.append("Plan for increased budget allocation")
                recommendations.append("Optimize high-volume operations")
                recommendations.append("Consider reserved capacity options")
            elif target_growth > 0.2:  # > 20% growth
                recommendations.append("Monitor costs closely during growth period")
                recommendations.append("Implement automated cost controls")
            
            # Budget recommendations
            recommended_budget = projected_monthly_cost * 1.2  # 20% buffer
            
            return {
                "target_growth": target_growth * 100,  # Convert to percentage
                "current_baseline": {
                    "monthly_cost": current_monthly_cost,
                    "monthly_requests": current_requests,
                    "average_cost_per_request": current_summary.average_cost_per_request
                },
                "projections": {
                    "monthly_cost": projected_monthly_cost,
                    "additional_cost": additional_cost,
                    "monthly_requests": projected_requests,
                    "additional_requests": additional_requests,
                    "cost_increase_percentage": (additional_cost / current_monthly_cost * 100) if current_monthly_cost > 0 else 0
                },
                "provider_breakdown": provider_projections,
                "budget_recommendations": {
                    "recommended_monthly_budget": recommended_budget,
                    "safety_margin": recommended_budget - projected_monthly_cost,
                    "budget_increase_needed": recommended_budget - current_monthly_cost
                },
                "capacity_requirements": {
                    "api_rate_limits": "Review and adjust for increased volume",
                    "connection_pools": "Scale connection pools proportionally",
                    "monitoring": "Enhance monitoring for higher volume"
                },
                "recommendations": recommendations,
                "risk_factors": [
                    "Growth may not be linear",
                    "Provider pricing may change",
                    "Usage patterns may shift with scale"
                ],
                "next_steps": [
                    "Create phased rollout plan",
                    "Establish growth monitoring dashboard",
                    "Set up automated budget alerts",
                    "Plan for quarterly budget reviews"
                ]
            }
            
        except Exception as e:
            logging.error(f"Capacity planning failed: {e}")
            raise ForecastingError(f"Capacity planning failed: {e}")


class UsageForecaster(CostPredictor):
    """Specialized forecaster for usage patterns and trends"""
    
    async def forecast_seasonal_patterns(self, provider: str) -> Dict[str, Any]:
        """Forecast seasonal usage patterns"""
        # Implementation for seasonal forecasting
        return await self.predict_usage_trends(provider)


class BudgetPlanner(CostPredictor):
    """Specialized planner for budget forecasting and planning"""
    
    async def recommend_budget_allocation(self, total_budget: float) -> Dict[str, Any]:
        """Recommend optimal budget allocation across providers"""
        # Get historical cost distribution
        summary = await self._cost_tracker.get_cost_summary()
        
        if summary.total_cost == 0:
            # Equal distribution if no history
            provider_count = len(summary.provider_costs) or 1
            allocation_per_provider = total_budget / provider_count
            
            return {
                "total_budget": total_budget,
                "allocation_strategy": "equal_distribution",
                "provider_allocations": {
                    "default": allocation_per_provider
                },
                "rationale": "No historical data available - using equal distribution"
            }
        
        # Proportional allocation based on historical usage
        allocations = {}
        for provider, cost in summary.provider_costs.items():
            proportion = cost / summary.total_cost
            allocations[provider] = total_budget * proportion
        
        return {
            "total_budget": total_budget,
            "allocation_strategy": "proportional_historical",
            "provider_allocations": allocations,
            "rationale": "Based on historical usage patterns"
        }


class CapacityPlanner(CostPredictor):
    """Specialized planner for capacity and infrastructure planning"""
    
    async def plan_infrastructure_scaling(self, growth_scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Plan infrastructure scaling for growth scenarios"""
        return await self.capacity_planning(growth_scenario.get("growth_rate", 0.5))
