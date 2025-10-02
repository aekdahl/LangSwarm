"""
LangSwarm V2 Billing System

Comprehensive billing and chargeback system with usage-based billing,
invoice generation, and departmental cost allocation capabilities.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import uuid
import json

from .interfaces import (
    ICostBillingSystem, BillingRecord, UsageRecord, BillingPeriod,
    CostEntry, BillingError
)


class BillingSystem(ICostBillingSystem):
    """
    Comprehensive billing and chargeback system.
    
    Provides usage-based billing, invoice generation, and departmental
    cost allocation with support for multiple billing models.
    """
    
    def __init__(self, cost_tracker, config: Dict[str, Any] = None):
        """
        Initialize billing system.
        
        Args:
            cost_tracker: Cost tracking system instance
            config: Billing configuration
        """
        self._cost_tracker = cost_tracker
        self._config = config or {}
        
        # Billing data storage
        self._billing_records: Dict[str, BillingRecord] = {}
        self._usage_records: List[UsageRecord] = []
        
        # Billing configuration
        self._billing_models = {
            "usage_based": self._calculate_usage_based_billing,
            "subscription": self._calculate_subscription_billing,
            "tiered": self._calculate_tiered_billing,
            "prepaid": self._calculate_prepaid_billing
        }
        
        # Pricing models
        self._pricing_models = self._load_pricing_models()
        
        # Invoice configuration
        self._invoice_config = {
            "currency": self._config.get("currency", "USD"),
            "tax_rate": self._config.get("tax_rate", 0.0),
            "payment_terms": self._config.get("payment_terms", 30),  # days
            "invoice_prefix": self._config.get("invoice_prefix", "INV"),
            "auto_send": self._config.get("auto_send", False)
        }
        
        logging.info("Initialized Billing System")
    
    def _load_pricing_models(self) -> Dict[str, Any]:
        """Load pricing models for different billing scenarios"""
        return {
            "enterprise": {
                "base_fee": 1000.0,  # Monthly base fee
                "included_tokens": 1000000,  # 1M tokens included
                "overage_rate": 0.001,  # $0.001 per token over limit
                "volume_discounts": {
                    5000000: 0.1,   # 10% discount over 5M tokens
                    10000000: 0.15, # 15% discount over 10M tokens
                    25000000: 0.2   # 20% discount over 25M tokens
                }
            },
            "professional": {
                "base_fee": 200.0,
                "included_tokens": 100000,  # 100K tokens included
                "overage_rate": 0.0015,
                "volume_discounts": {
                    1000000: 0.05,  # 5% discount over 1M tokens
                    2500000: 0.1    # 10% discount over 2.5M tokens
                }
            },
            "developer": {
                "base_fee": 50.0,
                "included_tokens": 10000,   # 10K tokens included
                "overage_rate": 0.002,
                "volume_discounts": {}
            },
            "pay_per_use": {
                "base_fee": 0.0,
                "included_tokens": 0,
                "overage_rate": 0.003,  # Higher rate for pure pay-per-use
                "volume_discounts": {}
            }
        }
    
    async def generate_bill(self, customer_id: str, 
                          period: BillingPeriod,
                          start_date: datetime,
                          end_date: datetime) -> BillingRecord:
        """
        Generate a bill for a customer.
        
        Args:
            customer_id: Customer identifier
            period: Billing period type
            start_date: Billing period start
            end_date: Billing period end
            
        Returns:
            Generated billing record
        """
        try:
            # Get usage data for the period
            usage_data = await self._get_customer_usage(customer_id, start_date, end_date)
            
            if not usage_data:
                logging.warning(f"No usage data found for customer {customer_id}")
                usage_data = []
            
            # Create billing record
            billing_record = BillingRecord(
                customer_id=customer_id,
                billing_period=period,
                period_start=start_date,
                period_end=end_date,
                currency=self._invoice_config["currency"]
            )
            
            # Calculate line items based on usage
            line_items = await self._calculate_line_items(customer_id, usage_data)
            billing_record.line_items = line_items
            
            # Calculate total amount
            billing_record.total_amount = sum(item["amount"] for item in line_items)
            
            # Apply taxes if configured
            if self._invoice_config["tax_rate"] > 0:
                tax_amount = billing_record.total_amount * self._invoice_config["tax_rate"]
                billing_record.line_items.append({
                    "description": f"Tax ({self._invoice_config['tax_rate']*100}%)",
                    "amount": tax_amount,
                    "category": "tax"
                })
                billing_record.total_amount += tax_amount
            
            # Store billing record
            self._billing_records[billing_record.record_id] = billing_record
            
            logging.info(f"Generated bill for customer {customer_id}: ${billing_record.total_amount:.2f}")
            
            return billing_record
            
        except Exception as e:
            logging.error(f"Failed to generate bill for customer {customer_id}: {e}")
            raise BillingError(f"Bill generation failed: {e}")
    
    async def _get_customer_usage(self, customer_id: str, start_date: datetime, end_date: datetime) -> List[UsageRecord]:
        """Get usage records for a customer in the specified period"""
        # Filter usage records for this customer and period
        customer_usage = []
        
        for record in self._usage_records:
            if (record.user_id == customer_id and 
                start_date <= record.timestamp <= end_date):
                customer_usage.append(record)
        
        return customer_usage
    
    async def _calculate_line_items(self, customer_id: str, usage_data: List[UsageRecord]) -> List[Dict[str, Any]]:
        """Calculate billing line items from usage data"""
        line_items = []
        
        # Get customer's pricing model
        pricing_model = await self._get_customer_pricing_model(customer_id)
        
        # Group usage by provider and model
        usage_by_provider = defaultdict(lambda: defaultdict(list))
        
        for record in usage_data:
            usage_by_provider[record.provider][record.model].append(record)
        
        # Calculate charges for each provider/model combination
        for provider, models in usage_by_provider.items():
            for model, records in models.items():
                # Aggregate usage
                total_tokens = sum(r.total_tokens for r in records)
                total_requests = sum(r.requests for r in records)
                total_cost = sum(r.cost for r in records)
                
                # Create line item
                line_item = {
                    "description": f"{provider} {model} Usage",
                    "provider": provider,
                    "model": model,
                    "quantity": total_tokens,
                    "unit": "tokens",
                    "requests": total_requests,
                    "amount": total_cost,
                    "period_start": min(r.timestamp for r in records).isoformat(),
                    "period_end": max(r.timestamp for r in records).isoformat(),
                    "category": "api_usage"
                }
                
                line_items.append(line_item)
        
        # Apply pricing model adjustments
        line_items = await self._apply_pricing_model(line_items, pricing_model)
        
        return line_items
    
    async def _get_customer_pricing_model(self, customer_id: str) -> Dict[str, Any]:
        """Get pricing model for a customer"""
        # This would typically look up customer's plan from a database
        # For now, return default model based on customer ID pattern
        if customer_id.startswith("enterprise_"):
            return self._pricing_models["enterprise"]
        elif customer_id.startswith("pro_"):
            return self._pricing_models["professional"]
        elif customer_id.startswith("dev_"):
            return self._pricing_models["developer"]
        else:
            return self._pricing_models["pay_per_use"]
    
    async def _apply_pricing_model(self, line_items: List[Dict[str, Any]], pricing_model: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply pricing model calculations to line items"""
        # Calculate total usage
        total_tokens = sum(item["quantity"] for item in line_items if item["unit"] == "tokens")
        
        # Apply base fee if applicable
        if pricing_model["base_fee"] > 0:
            line_items.insert(0, {
                "description": "Base Monthly Fee",
                "amount": pricing_model["base_fee"],
                "category": "base_fee"
            })
        
        # Apply included tokens
        included_tokens = pricing_model["included_tokens"]
        if included_tokens > 0 and total_tokens > included_tokens:
            overage_tokens = total_tokens - included_tokens
            overage_cost = overage_tokens * pricing_model["overage_rate"] / 1000  # Per 1K tokens
            
            line_items.append({
                "description": f"Overage Usage ({overage_tokens:,} tokens)",
                "quantity": overage_tokens,
                "unit": "tokens",
                "rate": pricing_model["overage_rate"],
                "amount": overage_cost,
                "category": "overage"
            })
        
        # Apply volume discounts
        volume_discounts = pricing_model.get("volume_discounts", {})
        if volume_discounts and total_tokens > 0:
            # Find applicable discount tier
            applicable_discount = 0.0
            for threshold, discount in sorted(volume_discounts.items()):
                if total_tokens >= threshold:
                    applicable_discount = discount
            
            if applicable_discount > 0:
                # Calculate discount amount
                usage_charges = sum(item["amount"] for item in line_items if item.get("category") in ["api_usage", "overage"])
                discount_amount = usage_charges * applicable_discount
                
                line_items.append({
                    "description": f"Volume Discount ({applicable_discount*100}%)",
                    "amount": -discount_amount,
                    "category": "discount"
                })
        
        return line_items
    
    async def calculate_chargeback(self, department: str, period: BillingPeriod) -> Dict[str, Any]:
        """
        Calculate chargeback costs for a department.
        
        Args:
            department: Department name
            period: Billing period
            
        Returns:
            Chargeback calculation details
        """
        try:
            # Calculate period dates
            end_date = datetime.utcnow()
            if period == BillingPeriod.MONTHLY:
                start_date = end_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            elif period == BillingPeriod.WEEKLY:
                days_since_monday = end_date.weekday()
                start_date = end_date - timedelta(days=days_since_monday)
                start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            elif period == BillingPeriod.DAILY:
                start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
            else:
                start_date = end_date - timedelta(days=30)  # Default to last 30 days
            
            # Get department usage
            department_usage = [
                record for record in self._usage_records
                if record.department == department and start_date <= record.timestamp <= end_date
            ]
            
            if not department_usage:
                return {
                    "department": department,
                    "period": period.value,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "total_cost": 0.0,
                    "breakdown": {},
                    "message": "No usage found for this department"
                }
            
            # Calculate chargeback breakdown
            breakdown = {}
            total_cost = 0.0
            
            # Group by user
            by_user = defaultdict(lambda: {"cost": 0.0, "tokens": 0, "requests": 0})
            for record in department_usage:
                by_user[record.user_id]["cost"] += record.cost
                by_user[record.user_id]["tokens"] += record.total_tokens
                by_user[record.user_id]["requests"] += record.requests
                total_cost += record.cost
            
            breakdown["by_user"] = dict(by_user)
            
            # Group by provider
            by_provider = defaultdict(lambda: {"cost": 0.0, "tokens": 0, "requests": 0})
            for record in department_usage:
                by_provider[record.provider]["cost"] += record.cost
                by_provider[record.provider]["tokens"] += record.total_tokens
                by_provider[record.provider]["requests"] += record.requests
            
            breakdown["by_provider"] = dict(by_provider)
            
            # Group by project
            by_project = defaultdict(lambda: {"cost": 0.0, "tokens": 0, "requests": 0})
            for record in department_usage:
                project = record.project_id or "unassigned"
                by_project[project]["cost"] += record.cost
                by_project[project]["tokens"] += record.total_tokens
                by_project[project]["requests"] += record.requests
            
            breakdown["by_project"] = dict(by_project)
            
            return {
                "department": department,
                "period": period.value,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "total_cost": total_cost,
                "total_tokens": sum(r.total_tokens for r in department_usage),
                "total_requests": sum(r.requests for r in department_usage),
                "breakdown": breakdown,
                "chargeback_rate": total_cost,  # Could apply department-specific rates
                "recommendations": self._generate_chargeback_recommendations(breakdown, total_cost)
            }
            
        except Exception as e:
            logging.error(f"Failed to calculate chargeback for department {department}: {e}")
            raise BillingError(f"Chargeback calculation failed: {e}")
    
    def _generate_chargeback_recommendations(self, breakdown: Dict[str, Any], total_cost: float) -> List[str]:
        """Generate recommendations for chargeback optimization"""
        recommendations = []
        
        # Analyze user usage patterns
        by_user = breakdown.get("by_user", {})
        if by_user:
            # Find high-cost users
            sorted_users = sorted(by_user.items(), key=lambda x: x[1]["cost"], reverse=True)
            top_user_cost = sorted_users[0][1]["cost"] if sorted_users else 0
            
            if top_user_cost > total_cost * 0.3:  # One user > 30% of total
                recommendations.append(f"Top user accounts for {(top_user_cost/total_cost)*100:.1f}% of costs - review usage patterns")
        
        # Analyze provider distribution
        by_provider = breakdown.get("by_provider", {})
        if len(by_provider) > 1:
            sorted_providers = sorted(by_provider.items(), key=lambda x: x[1]["cost"], reverse=True)
            if len(sorted_providers) >= 2:
                top_cost = sorted_providers[0][1]["cost"]
                second_cost = sorted_providers[1][1]["cost"]
                if top_cost > second_cost * 3:  # Highly concentrated
                    recommendations.append("Consider diversifying across providers for cost optimization")
        
        # Cost threshold recommendations
        if total_cost > 1000:
            recommendations.append("High monthly costs - consider implementing usage policies")
        elif total_cost > 500:
            recommendations.append("Moderate costs - monitor for optimization opportunities")
        
        if not recommendations:
            recommendations.append("Usage patterns appear balanced")
        
        return recommendations
    
    async def generate_invoice(self, billing_record_id: str) -> Dict[str, Any]:
        """
        Generate an invoice from a billing record.
        
        Args:
            billing_record_id: Billing record ID
            
        Returns:
            Invoice data
        """
        try:
            if billing_record_id not in self._billing_records:
                raise BillingError(f"Billing record not found: {billing_record_id}")
            
            billing_record = self._billing_records[billing_record_id]
            
            # Generate invoice number
            invoice_number = f"{self._invoice_config['invoice_prefix']}-{datetime.utcnow().strftime('%Y%m%d')}-{billing_record_id[:8]}"
            
            # Calculate due date
            invoice_date = datetime.utcnow()
            due_date = invoice_date + timedelta(days=self._invoice_config["payment_terms"])
            
            # Update billing record
            billing_record.invoice_number = invoice_number
            billing_record.invoice_date = invoice_date
            billing_record.due_date = due_date
            billing_record.status = "invoiced"
            
            # Create invoice data
            invoice = {
                "invoice_number": invoice_number,
                "billing_record_id": billing_record_id,
                "customer_id": billing_record.customer_id,
                "invoice_date": invoice_date.isoformat(),
                "due_date": due_date.isoformat(),
                "billing_period": {
                    "type": billing_record.billing_period.value,
                    "start": billing_record.period_start.isoformat(),
                    "end": billing_record.period_end.isoformat()
                },
                "line_items": billing_record.line_items,
                "subtotal": sum(item["amount"] for item in billing_record.line_items if item.get("category") != "tax"),
                "tax_amount": sum(item["amount"] for item in billing_record.line_items if item.get("category") == "tax"),
                "total_amount": billing_record.total_amount,
                "currency": billing_record.currency,
                "payment_terms": f"Net {self._invoice_config['payment_terms']} days",
                "status": "outstanding"
            }
            
            logging.info(f"Generated invoice {invoice_number} for ${billing_record.total_amount:.2f}")
            
            return invoice
            
        except Exception as e:
            logging.error(f"Failed to generate invoice for billing record {billing_record_id}: {e}")
            raise BillingError(f"Invoice generation failed: {e}")
    
    async def track_usage(self, usage: UsageRecord) -> None:
        """
        Track usage for billing purposes.
        
        Args:
            usage: Usage record to track
        """
        try:
            # Validate usage record
            if not usage.user_id:
                logging.warning("Usage record missing user_id")
                return
            
            if not usage.provider or not usage.model:
                logging.warning("Usage record missing provider or model")
                return
            
            # Store usage record
            self._usage_records.append(usage)
            
            # Keep only recent records (last 6 months)
            cutoff_date = datetime.utcnow() - timedelta(days=180)
            self._usage_records = [
                record for record in self._usage_records
                if record.timestamp >= cutoff_date
            ]
            
            logging.debug(f"Tracked usage: {usage.provider} {usage.model} - ${usage.cost:.4f}")
            
        except Exception as e:
            logging.error(f"Failed to track usage: {e}")
            raise BillingError(f"Usage tracking failed: {e}")
    
    async def get_billing_summary(self, customer_id: Optional[str] = None, 
                                period_days: int = 30) -> Dict[str, Any]:
        """Get billing summary for customer or all customers"""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=period_days)
            
            if customer_id:
                # Customer-specific summary
                customer_usage = await self._get_customer_usage(customer_id, start_date, end_date)
                
                total_cost = sum(record.cost for record in customer_usage)
                total_tokens = sum(record.total_tokens for record in customer_usage)
                total_requests = sum(record.requests for record in customer_usage)
                
                return {
                    "customer_id": customer_id,
                    "period": f"{period_days} days",
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "total_cost": total_cost,
                    "total_tokens": total_tokens,
                    "total_requests": total_requests,
                    "average_cost_per_token": total_cost / total_tokens if total_tokens > 0 else 0,
                    "average_cost_per_request": total_cost / total_requests if total_requests > 0 else 0,
                    "usage_records": len(customer_usage)
                }
            else:
                # Overall summary
                period_usage = [
                    record for record in self._usage_records
                    if start_date <= record.timestamp <= end_date
                ]
                
                total_cost = sum(record.cost for record in period_usage)
                unique_customers = len(set(record.user_id for record in period_usage))
                
                # Top customers
                customer_costs = defaultdict(float)
                for record in period_usage:
                    customer_costs[record.user_id] += record.cost
                
                top_customers = sorted(customer_costs.items(), key=lambda x: x[1], reverse=True)[:10]
                
                return {
                    "period": f"{period_days} days",
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "total_cost": total_cost,
                    "unique_customers": unique_customers,
                    "total_records": len(period_usage),
                    "average_cost_per_customer": total_cost / unique_customers if unique_customers > 0 else 0,
                    "top_customers": [{"customer_id": cid, "cost": cost} for cid, cost in top_customers]
                }
                
        except Exception as e:
            logging.error(f"Failed to get billing summary: {e}")
            return {"error": str(e)}


class UsageBillingSystem(BillingSystem):
    """Specialized billing system for pure usage-based billing"""
    
    async def _calculate_usage_based_billing(self, usage_data: List[UsageRecord]) -> float:
        """Calculate pure usage-based billing"""
        return sum(record.cost for record in usage_data)


class ChargebackSystem:
    """Specialized system for departmental chargebacks"""
    
    def __init__(self, billing_system: BillingSystem):
        """Initialize chargeback system"""
        self._billing_system = billing_system
        self._chargeback_rules: Dict[str, Dict[str, Any]] = {}
        self._allocation_methods = {
            "direct": self._direct_allocation,
            "proportional": self._proportional_allocation,
            "tiered": self._tiered_allocation
        }
    
    def set_chargeback_rules(self, department: str, rules: Dict[str, Any]) -> None:
        """Set chargeback rules for a department"""
        self._chargeback_rules[department] = rules
    
    async def _direct_allocation(self, usage_data: List[UsageRecord]) -> Dict[str, float]:
        """Direct allocation - charge actual costs to departments"""
        department_costs = defaultdict(float)
        for record in usage_data:
            if record.department:
                department_costs[record.department] += record.cost
        return dict(department_costs)
    
    async def _proportional_allocation(self, usage_data: List[UsageRecord]) -> Dict[str, float]:
        """Proportional allocation based on usage ratios"""
        # Implementation for proportional allocation
        return await self._direct_allocation(usage_data)
    
    async def _tiered_allocation(self, usage_data: List[UsageRecord]) -> Dict[str, float]:
        """Tiered allocation with different rates per tier"""
        # Implementation for tiered allocation
        return await self._direct_allocation(usage_data)
    
    async def generate_chargeback_report(self, period: BillingPeriod) -> Dict[str, Any]:
        """Generate comprehensive chargeback report"""
        # Get all departments
        departments = set()
        for record in self._billing_system._usage_records:
            if record.department:
                departments.add(record.department)
        
        # Calculate chargebacks for each department
        chargeback_data = {}
        total_chargeback = 0.0
        
        for department in departments:
            chargeback = await self._billing_system.calculate_chargeback(department, period)
            chargeback_data[department] = chargeback
            total_chargeback += chargeback["total_cost"]
        
        return {
            "period": period.value,
            "total_departments": len(departments),
            "total_chargeback_amount": total_chargeback,
            "department_chargebacks": chargeback_data,
            "generated_at": datetime.utcnow().isoformat()
        }


class InvoiceGenerator:
    """Specialized invoice generation and formatting"""
    
    def __init__(self, billing_system: BillingSystem):
        """Initialize invoice generator"""
        self._billing_system = billing_system
        self._templates = {
            "html": self._generate_html_invoice,
            "pdf": self._generate_pdf_invoice,
            "json": self._generate_json_invoice
        }
    
    async def generate_formatted_invoice(self, billing_record_id: str, format: str = "html") -> str:
        """Generate formatted invoice in specified format"""
        invoice_data = await self._billing_system.generate_invoice(billing_record_id)
        
        if format in self._templates:
            return await self._templates[format](invoice_data)
        else:
            raise BillingError(f"Unsupported invoice format: {format}")
    
    async def _generate_html_invoice(self, invoice_data: Dict[str, Any]) -> str:
        """Generate HTML invoice"""
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Invoice {invoice_data['invoice_number']}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .header {{ text-align: center; margin-bottom: 30px; }}
                .invoice-details {{ margin-bottom: 20px; }}
                table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .total {{ font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>INVOICE</h1>
                <h2>{invoice_data['invoice_number']}</h2>
            </div>
            
            <div class="invoice-details">
                <p><strong>Customer ID:</strong> {invoice_data['customer_id']}</p>
                <p><strong>Invoice Date:</strong> {invoice_data['invoice_date']}</p>
                <p><strong>Due Date:</strong> {invoice_data['due_date']}</p>
                <p><strong>Billing Period:</strong> {invoice_data['billing_period']['start']} to {invoice_data['billing_period']['end']}</p>
            </div>
            
            <table>
                <thead>
                    <tr>
                        <th>Description</th>
                        <th>Quantity</th>
                        <th>Amount</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for item in invoice_data['line_items']:
            quantity = item.get('quantity', '-')
            html_template += f"""
                    <tr>
                        <td>{item.get('description', '')}</td>
                        <td>{quantity}</td>
                        <td>${item['amount']:.2f}</td>
                    </tr>
            """
        
        html_template += f"""
                </tbody>
            </table>
            
            <div class="total">
                <p><strong>Total Amount: ${invoice_data['total_amount']:.2f} {invoice_data['currency']}</strong></p>
                <p>Payment Terms: {invoice_data['payment_terms']}</p>
            </div>
        </body>
        </html>
        """
        
        return html_template
    
    async def _generate_pdf_invoice(self, invoice_data: Dict[str, Any]) -> str:
        """Generate PDF invoice (placeholder - would use library like ReportLab)"""
        # For now, return HTML version
        return await self._generate_html_invoice(invoice_data)
    
    async def _generate_json_invoice(self, invoice_data: Dict[str, Any]) -> str:
        """Generate JSON invoice"""
        return json.dumps(invoice_data, indent=2, default=str)
