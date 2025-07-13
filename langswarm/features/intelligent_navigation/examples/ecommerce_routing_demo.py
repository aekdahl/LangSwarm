#!/usr/bin/env python3
"""
E-commerce Navigation Demo

This demo shows weighted navigation and customer tier-based routing for an e-commerce platform.
It demonstrates:
- Weighted probabilistic routing
- Customer tier preferences
- Order status and product support routing
- Performance optimization
"""

import random
import time
from datetime import datetime
from typing import Dict, Any, List

from ..navigator import NavigationTool, WorkflowNavigator, NavigationContext
from ..schema import create_navigation_config, NavigationMode, ConditionOperator
from ..tracker import NavigationTracker


class EcommerceRoutingDemo:
    """Demo class for e-commerce navigation with weighted routing"""
    
    def __init__(self):
        self.navigator = WorkflowNavigator("ecommerce_demo.db")
        self.tool = NavigationTool(self.navigator)
        self.setup_configuration()
    
    def setup_configuration(self):
        """Set up weighted navigation configuration for e-commerce"""
        # Build configuration with weighted routing
        config_builder = (create_navigation_config()
                         .set_mode(NavigationMode.WEIGHTED)
                         
                         # Order management - high weight for post-purchase issues
                         .add_condition_step(
                             "order_management",
                             "Order Management",
                             "Handle order status, shipping, and delivery issues efficiently",
                             "output.intent", "contains", "order",
                             weight=3.0  # High weight - prioritize order issues
                         )
                         
                         # Product support - medium-high weight for product questions
                         .add_condition_step(
                             "product_support",
                             "Product Support", 
                             "Handle product questions, returns, exchanges, and technical product issues",
                             "output.intent", "contains", "product",
                             weight=2.5
                         )
                         
                         # Payment issues - high priority for payment problems
                         .add_condition_step(
                             "payment_support",
                             "Payment Support",
                             "Resolve payment failures, refunds, and billing disputes",
                             "output.category", "eq", "payment",
                             weight=2.8
                         )
                         
                         # Sales inquiries - medium weight, good for upselling
                         .add_step(
                             "sales_inquiry",
                             "Sales Inquiry",
                             "Handle pre-purchase questions and product recommendations",
                             weight=2.0
                         )
                         
                         # Account management - lower weight unless specific conditions
                         .add_condition_step(
                             "account_management",
                             "Account Management",
                             "Handle account settings, profile updates, and preferences",
                             "output.intent", "contains", "account",
                             weight=1.5
                         )
                         
                         # VIP support - lower base weight but high priority for VIP customers
                         .add_step(
                             "vip_support",
                             "VIP Concierge Support",
                             "Premium white-glove support for VIP customers",
                             weight=1.0  # Base weight, increased by rules
                         )
                         
                         .set_fallback("sales_inquiry")  # Sales as fallback
                         .set_timeout(25)  # Faster timeout for e-commerce
                         .set_tracking(True))
        
        # Add conditional rules for customer tier routing
        from ..schema import NavigationCondition
        
        # Rule 1: VIP customers get routed to VIP support regardless of issue
        vip_conditions = [
            NavigationCondition("output.customer_tier", ConditionOperator.EQUALS, "vip")
        ]
        config_builder.add_rule("vip_support", vip_conditions, priority=10,
                               description="VIP customers always get premium support")
        
        # Rule 2: High-value orders get priority order management
        high_value_conditions = [
            NavigationCondition("output.order_value", ConditionOperator.GT, 500.0),
            NavigationCondition("output.intent", ConditionOperator.CONTAINS, "order")
        ]
        config_builder.add_rule("order_management", high_value_conditions, priority=8,
                               description="High-value orders get priority handling")
        
        # Rule 3: Payment failures get immediate attention
        payment_failure_conditions = [
            NavigationCondition("output.payment_status", ConditionOperator.EQUALS, "failed")
        ]
        config_builder.add_rule("payment_support", payment_failure_conditions, priority=9,
                               description="Payment failures need immediate resolution")
        
        self.config = config_builder.build()
        print("✅ E-commerce weighted navigation configuration ready")
    
    def simulate_ecommerce_scenarios(self, num_scenarios: int = 20) -> List[Dict[str, Any]]:
        """Simulate various e-commerce customer scenarios"""
        scenarios = []
        
        # Define realistic e-commerce scenario templates
        scenario_templates = [
            {
                "type": "order_tracking",
                "intents": ["order", "shipping", "delivery", "tracking"],
                "categories": ["order", "shipping"],
                "customer_tiers": ["standard", "premium", "vip"],
                "priorities": ["normal", "high"],
                "descriptions": [
                    "Where is my order?",
                    "Order hasn't arrived yet",
                    "Need shipping update",
                    "Tracking shows incorrect status"
                ]
            },
            {
                "type": "product_questions",
                "intents": ["product", "features", "compatibility", "specs"],
                "categories": ["product", "technical"],
                "customer_tiers": ["standard", "premium"],
                "priorities": ["low", "normal"],
                "descriptions": [
                    "Product compatibility question",
                    "How does this feature work?",
                    "Product specifications inquiry",
                    "Need product recommendations"
                ]
            },
            {
                "type": "payment_issues",
                "intents": ["payment", "billing", "refund", "charge"],
                "categories": ["payment", "billing"],
                "customer_tiers": ["standard", "premium", "vip"],
                "priorities": ["high", "urgent"],
                "descriptions": [
                    "Payment failed during checkout",
                    "Unauthorized charge on account",
                    "Refund not processed",
                    "Payment method declined"
                ]
            },
            {
                "type": "sales_inquiry",
                "intents": ["buy", "purchase", "recommend", "compare"],
                "categories": ["sales", "inquiry"],
                "customer_tiers": ["standard", "premium"],
                "priorities": ["normal"],
                "descriptions": [
                    "Looking for product recommendations",
                    "Want to compare products",
                    "Ready to make a purchase",
                    "Need help choosing"
                ]
            },
            {
                "type": "returns_exchanges",
                "intents": ["return", "exchange", "defective", "wrong"],
                "categories": ["return", "product"],
                "customer_tiers": ["standard", "premium", "vip"],
                "priorities": ["normal", "high"],
                "descriptions": [
                    "Need to return defective item",
                    "Wrong item received",
                    "Want to exchange for different size",
                    "Product not as described"
                ]
            }
        ]
        
        for i in range(num_scenarios):
            template = random.choice(scenario_templates)
            
            # Generate realistic scenario data
            scenario = {
                "scenario_id": f"ecom_{i:03d}",
                "type": template["type"],
                "description": random.choice(template["descriptions"]),
                "context": {
                    "output": {
                        "intent": random.choice(template["intents"]),
                        "category": random.choice(template["categories"]),
                        "customer_tier": random.choice(template["customer_tiers"]),
                        "priority": random.choice(template["priorities"]),
                        "order_value": random.uniform(25.0, 1000.0),
                        "payment_status": random.choice(["success", "failed", "pending"]),
                        "user_sentiment": random.uniform(0.2, 0.9),
                        "session_length": random.randint(60, 1800)  # seconds
                    },
                    "customer": {
                        "purchase_history": random.randint(0, 50),
                        "avg_order_value": random.uniform(50.0, 300.0),
                        "satisfaction_score": random.uniform(3.0, 5.0)
                    }
                }
            }
            scenarios.append(scenario)
        
        return scenarios
    
    def run_navigation_simulation(self, scenarios: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Run navigation simulation for all scenarios"""
        print(f"\n🛒 Running E-commerce Navigation Simulation")
        print(f"📊 Processing {len(scenarios)} customer scenarios...")
        print("=" * 60)
        
        results = []
        route_distribution = {}
        
        for scenario in scenarios:
            # Set up navigation context
            context = NavigationContext(
                workflow_id="ecommerce_routing_demo",
                current_step="customer_routing",
                context_data=scenario["context"],
                step_history=[],
                available_steps=[
                    {"id": "order_management"},
                    {"id": "product_support"},
                    {"id": "payment_support"},
                    {"id": "sales_inquiry"},
                    {"id": "account_management"},
                    {"id": "vip_support"}
                ]
            )
            
            self.tool.set_context(self.config, context)
            
            # Simulate intelligent routing decision
            step_id, reasoning, confidence = self.make_intelligent_routing_decision(scenario)
            
            # Execute navigation
            start_time = time.time()
            result = self.tool.execute({
                "step_id": step_id,
                "reasoning": reasoning,
                "confidence": confidence
            })
            execution_time = (time.time() - start_time) * 1000
            
            # Track routing distribution
            chosen_step = result["tool"]["chosen_step"]
            route_distribution[chosen_step] = route_distribution.get(chosen_step, 0) + 1
            
            # Store result
            result_data = {
                "scenario_id": scenario["scenario_id"],
                "scenario_type": scenario["type"],
                "customer_tier": scenario["context"]["output"]["customer_tier"],
                "chosen_route": chosen_step,
                "confidence": confidence,
                "execution_time_ms": execution_time,
                "success": result["tool"]["status"] == "success"
            }
            results.append(result_data)
            
            # Show progress for first few scenarios
            if len(results) <= 5:
                tier = scenario["context"]["output"]["customer_tier"]
                intent = scenario["context"]["output"]["intent"]
                print(f"📞 Scenario {len(results):2d}: {tier} customer with {intent} → {chosen_step}")
        
        # Show routing distribution
        print(f"\n📈 Routing Distribution:")
        total_scenarios = len(scenarios)
        for route, count in sorted(route_distribution.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_scenarios) * 100
            print(f"   {route}: {count} scenarios ({percentage:.1f}%)")
        
        return results
    
    def make_intelligent_routing_decision(self, scenario: Dict[str, Any]) -> tuple:
        """Make an intelligent routing decision based on scenario context"""
        context_data = scenario["context"]["output"]
        
        intent = context_data["intent"]
        category = context_data["category"]
        customer_tier = context_data["customer_tier"]
        priority = context_data["priority"]
        order_value = context_data["order_value"]
        payment_status = context_data["payment_status"]
        
        # Decision logic with confidence scoring
        if customer_tier == "vip":
            return "vip_support", f"VIP customer gets premium white-glove support", 0.95
        
        elif payment_status == "failed":
            return "payment_support", f"Payment failure requires immediate resolution", 0.9
        
        elif "order" in intent and order_value > 500:
            return "order_management", f"High-value order (${order_value:.0f}) needs priority handling", 0.88
        
        elif "order" in intent or "shipping" in intent or "delivery" in intent:
            return "order_management", f"Order-related inquiry routed to fulfillment specialists", 0.85
        
        elif "product" in intent or category == "product":
            return "product_support", f"Product inquiry needs specialist product knowledge", 0.8
        
        elif category == "payment" or "payment" in intent:
            return "payment_support", f"Payment issue requires billing specialist", 0.82
        
        elif "account" in intent:
            return "account_management", f"Account-related request for profile management", 0.75
        
        else:
            return "sales_inquiry", f"General inquiry routed to sales for potential upselling", 0.7
    
    def analyze_performance(self, results: List[Dict[str, Any]]):
        """Analyze navigation performance"""
        print(f"\n📊 Performance Analysis")
        print("=" * 60)
        
        # Overall metrics
        total_scenarios = len(results)
        successful_routes = len([r for r in results if r["success"]])
        avg_confidence = sum(r["confidence"] for r in results) / total_scenarios
        avg_execution_time = sum(r["execution_time_ms"] for r in results) / total_scenarios
        
        print(f"✅ Success Rate: {successful_routes}/{total_scenarios} ({(successful_routes/total_scenarios)*100:.1f}%)")
        print(f"🎯 Average Confidence: {avg_confidence:.1%}")
        print(f"⚡ Average Decision Time: {avg_execution_time:.1f}ms")
        
        # Customer tier analysis
        tier_stats = {}
        for result in results:
            tier = result["customer_tier"]
            if tier not in tier_stats:
                tier_stats[tier] = {"count": 0, "confidence_sum": 0, "time_sum": 0}
            
            tier_stats[tier]["count"] += 1
            tier_stats[tier]["confidence_sum"] += result["confidence"]
            tier_stats[tier]["time_sum"] += result["execution_time_ms"]
        
        print(f"\n👥 Customer Tier Performance:")
        for tier, stats in tier_stats.items():
            count = stats["count"]
            avg_conf = stats["confidence_sum"] / count
            avg_time = stats["time_sum"] / count
            print(f"   {tier.upper()}: {count} scenarios, {avg_conf:.1%} confidence, {avg_time:.1f}ms avg")
        
        # Get navigation analytics
        analytics = self.navigator.tracker.get_analytics(
            workflow_id="ecommerce_routing_demo",
            days=1
        )
        
        print(f"\n🎯 Top Routing Paths:")
        for i, path in enumerate(analytics.most_common_paths[:5], 1):
            print(f"   {i}. {path['path']} ({path['percentage']:.1f}% of traffic)")
        
        if analytics.optimization_suggestions:
            print(f"\n💡 Optimization Suggestions:")
            for i, suggestion in enumerate(analytics.optimization_suggestions, 1):
                print(f"   {i}. {suggestion}")
    
    def demonstrate_weight_impact(self):
        """Demonstrate how weights affect routing distribution"""
        print(f"\n⚖️  Weight Impact Demonstration")
        print("=" * 60)
        
        # Show current step weights
        print("Current step weights:")
        for step in self.config.available_steps:
            print(f"   {step.name}: {step.weight}")
        
        print(f"\nWeighted routing means steps with higher weights are more likely to be chosen")
        print(f"when multiple steps match the current context conditions.")
        
        # Simulate weighted selection
        available_steps = [
            ("order_management", 3.0),
            ("product_support", 2.5), 
            ("payment_support", 2.8),
            ("sales_inquiry", 2.0),
            ("account_management", 1.5),
            ("vip_support", 1.0)
        ]
        
        total_weight = sum(weight for _, weight in available_steps)
        print(f"\nProbability distribution (if all steps were available):")
        for step_name, weight in available_steps:
            probability = (weight / total_weight) * 100
            print(f"   {step_name}: {probability:.1f}%")


def main():
    """Main demo function"""
    print("🧭 LangSwarm Intelligent Navigation System")
    print("🛒 E-commerce Weighted Routing Demo")
    print()
    
    demo = EcommerceRoutingDemo()
    
    try:
        # Generate scenarios
        scenarios = demo.simulate_ecommerce_scenarios(num_scenarios=25)
        
        # Run navigation simulation
        results = demo.run_navigation_simulation(scenarios)
        
        # Analyze performance
        demo.analyze_performance(results)
        
        # Demonstrate weight impact
        demo.demonstrate_weight_impact()
        
        print(f"\n🎉 E-commerce demo completed successfully!")
        print(f"📊 Analytics data saved to: ecommerce_demo.db")
        
    except Exception as e:
        print(f"❌ Demo error: {e}")
        raise


if __name__ == "__main__":
    main() 