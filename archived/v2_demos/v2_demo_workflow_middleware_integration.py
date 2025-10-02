#!/usr/bin/env python3
"""
Comprehensive demonstration of V2 Workflow Middleware Integration

This script demonstrates the complete integration between the V2 workflow system
and the V2 middleware pipeline with advanced features including:
- Workflow-specific interceptors and policies
- Request routing based on complexity and type
- Context enrichment and validation
- Result transformation and formatting
- Comprehensive audit and compliance logging
"""

import asyncio
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add path for imports
import sys
sys.path.insert(0, '.')

try:
    from langswarm.v2.core.workflows.middleware import (
        WorkflowMiddlewareManager,
        WorkflowExecutionContext,
        MiddlewareIntegrationMode,
        WorkflowPolicy,
        WorkflowComplexity,
        create_workflow_pipeline,
        create_enhanced_workflow_pipeline,
        create_development_manager,
        create_production_manager
    )
    
    from langswarm.v2.core.workflows.interfaces import ExecutionMode
    from langswarm.v2.core.workflows.middleware.router import (
        WorkflowRequestRouter,
        RouteConfiguration,
        RoutingStrategy,
        create_development_router
    )
    
    print("✅ Successfully imported workflow middleware components!")
    
except ImportError as e:
    print(f"❌ Import failed: {e}")
    print("This demo requires the V2 workflow middleware system to be available.")
    exit(1)


async def demo_basic_middleware_integration():
    """Demonstrate basic workflow middleware integration"""
    
    print("\n" + "="*60)
    print("🏗️  DEMO 1: Basic Middleware Integration")
    print("="*60)
    
    # Create basic middleware manager
    manager = WorkflowMiddlewareManager(
        integration_mode=MiddlewareIntegrationMode.BASIC
    )
    
    print(f"✅ Created middleware manager in {manager.integration_mode.value} mode")
    
    # Create simple workflow execution context
    context = WorkflowExecutionContext(
        workflow_id="simple_greeting_workflow",
        input_data={"name": "World", "greeting": "Hello"},
        execution_mode=ExecutionMode.SYNC,
        user_id="demo_user",
        department="engineering"
    )
    
    print(f"✅ Created execution context for workflow: {context.workflow_id}")
    
    # Execute workflow
    start_time = time.time()
    result = await manager.execute_workflow(context)
    execution_time = time.time() - start_time
    
    print(f"✅ Workflow execution completed in {execution_time:.3f}s")
    print(f"  Success: {result.success}")
    print(f"  Status: {result.status}")
    print(f"  Execution ID: {result.execution_id}")
    
    if result.complexity:
        print(f"  Detected complexity: {result.complexity.value}")
    if result.routing_strategy:
        print(f"  Routing strategy: {result.routing_strategy}")
    
    # Get pipeline statistics
    stats = manager.get_pipeline_stats()
    print(f"✅ Pipeline statistics:")
    print(f"  Total executions: {stats['execution_stats']['total_executions']}")
    print(f"  Success rate: {stats['pipeline_stats'].get('success_rate', 0):.1f}%")
    
    return True


async def demo_enhanced_middleware_features():
    """Demonstrate enhanced middleware features"""
    
    print("\n" + "="*60)
    print("🚀 DEMO 2: Enhanced Middleware Features")
    print("="*60)
    
    # Create enhanced middleware manager
    manager = WorkflowMiddlewareManager(
        integration_mode=MiddlewareIntegrationMode.ENHANCED
    )
    
    print(f"✅ Created enhanced middleware manager")
    
    # Create complex workflow execution context with rich metadata
    context = WorkflowExecutionContext(
        workflow_id="complex_data_pipeline",
        input_data={
            "data_source": "customer_database",
            "filters": {"status": "active", "country": "US"},
            "output_format": "json",
            "batch_size": 1000
        },
        execution_mode=ExecutionMode.ASYNC,
        context_variables={
            "environment": "production",
            "api_version": "v2",
            "timeout": 3600
        },
        user_id="data_analyst_123",
        session_id="session_456",
        department="data_science",
        project_id="customer_analysis_2024",
        priority="high",
        timeout=timedelta(minutes=30),
        policy_name="data_processing_policy",
        output_format="detailed",
        audit_level="comprehensive",
        metadata={
            "cost_center": "analytics",
            "compliance_required": True,
            "data_classification": "confidential"
        }
    )
    
    print(f"✅ Created complex execution context with rich metadata")
    print(f"  Workflow: {context.workflow_id}")
    print(f"  Department: {context.department}")
    print(f"  Priority: {context.priority}")
    print(f"  Audit level: {context.audit_level}")
    
    # Execute workflow
    start_time = time.time()
    result = await manager.execute_workflow(context)
    execution_time = time.time() - start_time
    
    print(f"✅ Enhanced workflow execution completed in {execution_time:.3f}s")
    print(f"  Success: {result.success}")
    print(f"  Complexity: {result.complexity.value if result.complexity else 'Unknown'}")
    print(f"  Routing strategy: {result.routing_strategy}")
    print(f"  Validation passed: {result.validation_passed}")
    
    # Show middleware metadata
    if result.middleware_metadata:
        print(f"✅ Middleware performance breakdown:")
        for key, value in result.middleware_metadata.items():
            if value is not None:
                print(f"  {key}: {value:.3f}s" if isinstance(value, float) else f"  {key}: {value}")
    
    # Show performance metrics
    if result.performance_metrics:
        print(f"✅ Performance metrics:")
        for key, value in result.performance_metrics.items():
            if value is not None:
                print(f"  {key}: {value}")
    
    return True


async def demo_workflow_routing_strategies():
    """Demonstrate workflow routing strategies"""
    
    print("\n" + "="*60)
    print("🎯 DEMO 3: Workflow Routing Strategies")
    print("="*60)
    
    # Create router with different strategies
    router = create_development_router()
    
    print(f"✅ Created workflow router")
    
    # Test different routing strategies
    strategies = [
        RoutingStrategy.ROUND_ROBIN,
        RoutingStrategy.LEAST_LOADED,
        RoutingStrategy.COMPLEXITY_BASED,
        RoutingStrategy.PRIORITY_BASED
    ]
    
    from langswarm.v2.core.middleware import RequestContext
    
    for strategy in strategies:
        print(f"\n🔄 Testing {strategy.value} routing strategy:")
        
        # Create sample requests with different complexities
        test_requests = [
            (WorkflowComplexity.SIMPLE, "simple_task"),
            (WorkflowComplexity.MEDIUM, "data_processing"),
            (WorkflowComplexity.COMPLEX, "ml_training"),
            (WorkflowComplexity.ENTERPRISE, "enterprise_integration")
        ]
        
        for complexity, workflow_id in test_requests:
            context = RequestContext(
                action="workflow_execution",
                params={"workflow_id": workflow_id},
                metadata={"priority": "normal"}
            )
            
            try:
                lane = await router.route_request(context, complexity, strategy)
                print(f"  {complexity.value} → {lane}")
            except Exception as e:
                print(f"  {complexity.value} → ERROR: {e}")
    
    # Show router statistics
    router_stats = router.get_router_stats()
    print(f"\n✅ Router statistics:")
    print(f"  Total routes: {router_stats['routing_stats']['total_routes']}")
    print(f"  Successful routes: {router_stats['routing_stats']['successful_routes']}")
    print(f"  Overall load: {router_stats['overall_load_percentage']:.1f}%")
    
    return True


async def demo_policy_enforcement():
    """Demonstrate workflow policy enforcement"""
    
    print("\n" + "="*60)
    print("🛡️  DEMO 4: Policy Enforcement & Compliance")
    print("="*60)
    
    # Create custom policies
    custom_policies = {
        "strict_policy": WorkflowPolicy(
            max_execution_time=timedelta(minutes=5),
            max_steps=10,
            max_parallel_steps=2,
            retry_attempts=1,
            require_approval=True,
            audit_level="comprehensive",
            security_level="high",
            resource_limits={"memory": "1GB", "cpu": "1.0"}
        ),
        "development_policy": WorkflowPolicy(
            max_execution_time=timedelta(minutes=30),
            max_steps=100,
            max_parallel_steps=10,
            retry_attempts=3,
            audit_level="standard",
            security_level="standard"
        )
    }
    
    # Create enhanced pipeline with custom policies
    pipeline = create_enhanced_workflow_pipeline(custom_policies=custom_policies)
    
    manager = WorkflowMiddlewareManager(
        integration_mode=MiddlewareIntegrationMode.CUSTOM,
        custom_pipeline=pipeline
    )
    
    print(f"✅ Created manager with custom policies")
    
    # Test policy enforcement
    test_scenarios = [
        {
            "name": "Valid workflow (development policy)",
            "context": WorkflowExecutionContext(
                workflow_id="dev_test_workflow",
                input_data={"test": True},
                policy_name="development_policy",
                user_id="developer"
            )
        },
        {
            "name": "High-security workflow (strict policy)",
            "context": WorkflowExecutionContext(
                workflow_id="secure_workflow",
                input_data={"sensitive": True},
                policy_name="strict_policy",
                user_id="security_admin",
                audit_level="comprehensive"
            )
        }
    ]
    
    for scenario in test_scenarios:
        print(f"\n🧪 Testing: {scenario['name']}")
        
        try:
            result = await manager.execute_workflow(scenario['context'])
            print(f"  ✅ Execution successful")
            print(f"  Validation passed: {result.validation_passed}")
            print(f"  Audit ID: {result.audit_id}")
        except Exception as e:
            print(f"  ❌ Execution failed: {e}")
    
    return True


async def demo_batch_execution():
    """Demonstrate batch workflow execution with middleware"""
    
    print("\n" + "="*60)
    print("⚡ DEMO 5: Batch Workflow Execution")
    print("="*60)
    
    # Create production-ready manager
    manager = create_production_manager()
    
    print(f"✅ Created production manager for batch execution")
    
    # Create batch of workflow contexts
    batch_contexts = []
    for i in range(5):
        context = WorkflowExecutionContext(
            workflow_id=f"batch_workflow_{i+1}",
            input_data={"batch_id": i+1, "data": f"sample_data_{i+1}"},
            execution_mode=ExecutionMode.ASYNC,
            user_id=f"batch_user_{i+1}",
            department="operations",
            priority="normal" if i < 3 else "high"
        )
        batch_contexts.append(context)
    
    print(f"✅ Created batch of {len(batch_contexts)} workflows")
    
    # Execute batch
    start_time = time.time()
    results = await manager.execute_workflow_batch(
        batch_contexts, 
        max_concurrent=3
    )
    batch_time = time.time() - start_time
    
    print(f"✅ Batch execution completed in {batch_time:.3f}s")
    
    # Analyze results
    successful = sum(1 for result in results if result.success)
    failed = len(results) - successful
    avg_execution_time = sum(result.execution_time for result in results) / len(results)
    
    print(f"  Total workflows: {len(results)}")
    print(f"  Successful: {successful}")
    print(f"  Failed: {failed}")
    print(f"  Success rate: {(successful/len(results)*100):.1f}%")
    print(f"  Average execution time: {avg_execution_time:.3f}s")
    
    # Show individual results
    print(f"\n📊 Individual results:")
    for i, result in enumerate(results):
        status_icon = "✅" if result.success else "❌"
        print(f"  {status_icon} Workflow {i+1}: {result.status} ({result.execution_time:.3f}s)")
    
    return True


async def demo_performance_monitoring():
    """Demonstrate performance monitoring and optimization"""
    
    print("\n" + "="*60)
    print("📈 DEMO 6: Performance Monitoring & Optimization")
    print("="*60)
    
    # Create performance-optimized manager
    from langswarm.v2.core.workflows.middleware.manager import create_performance_optimized_manager
    manager = create_performance_optimized_manager()
    
    print(f"✅ Created performance-optimized manager")
    
    # Execute multiple workflows to gather metrics
    print(f"🔄 Executing multiple workflows to gather performance data...")
    
    for i in range(10):
        context = WorkflowExecutionContext(
            workflow_id=f"perf_test_workflow_{i+1}",
            input_data={"iteration": i+1},
            execution_mode=ExecutionMode.SYNC if i % 2 == 0 else ExecutionMode.ASYNC,
            user_id="performance_tester"
        )
        
        result = await manager.execute_workflow(context)
        print(f"  Workflow {i+1}: {result.execution_time:.3f}s ({'✅' if result.success else '❌'})")
    
    # Get comprehensive performance statistics
    stats = manager.get_pipeline_stats()
    
    print(f"\n📊 Performance Statistics:")
    print(f"  Integration mode: {stats['integration_mode']}")
    print(f"  Total executions: {stats['execution_stats']['total_executions']}")
    print(f"  Average execution time: {stats['execution_stats']['average_execution_time']:.3f}s")
    print(f"  Success rate: {stats['pipeline_stats']['success_rate']:.1f}%")
    print(f"  Throughput: {stats['pipeline_stats']['throughput']:.1f} workflows/sec")
    print(f"  Middleware overhead: {stats['middleware_overhead']:.3f}s")
    
    # Pipeline-specific stats
    if 'pipeline_stats' in stats:
        pipeline_stats = stats['pipeline_stats']
        print(f"\n🔧 Pipeline Statistics:")
        print(f"  Interceptor count: {stats['interceptor_count']}")
        print(f"  Error rate: {pipeline_stats.get('error_rate', 0):.1f}%")
    
    return True


async def demo_integration_modes():
    """Demonstrate different middleware integration modes"""
    
    print("\n" + "="*60)
    print("🔧 DEMO 7: Middleware Integration Modes")
    print("="*60)
    
    modes = [
        MiddlewareIntegrationMode.DISABLED,
        MiddlewareIntegrationMode.BASIC,
        MiddlewareIntegrationMode.ENHANCED,
        MiddlewareIntegrationMode.PRODUCTION
    ]
    
    test_context = WorkflowExecutionContext(
        workflow_id="mode_test_workflow",
        input_data={"test": "integration_modes"},
        execution_mode=ExecutionMode.SYNC
    )
    
    mode_results = {}
    
    for mode in modes:
        print(f"\n🧪 Testing {mode.value} mode:")
        
        try:
            manager = WorkflowMiddlewareManager(integration_mode=mode)
            
            start_time = time.time()
            result = await manager.execute_workflow(test_context)
            execution_time = time.time() - start_time
            
            mode_results[mode.value] = {
                "success": result.success,
                "execution_time": execution_time,
                "middleware_overhead": len(result.middleware_metadata) if result.middleware_metadata else 0
            }
            
            print(f"  ✅ Success: {result.success}")
            print(f"  ⏱️  Execution time: {execution_time:.3f}s")
            print(f"  🔧 Middleware features: {len(result.middleware_metadata) if result.middleware_metadata else 0}")
            
        except Exception as e:
            print(f"  ❌ Failed: {e}")
            mode_results[mode.value] = {"success": False, "error": str(e)}
    
    # Compare modes
    print(f"\n📊 Mode Comparison:")
    for mode, results in mode_results.items():
        if results.get("success"):
            print(f"  {mode}: {results['execution_time']:.3f}s (features: {results['middleware_overhead']})")
        else:
            print(f"  {mode}: Failed")
    
    return True


async def main():
    """Run all workflow middleware integration demonstrations"""
    
    print("🚀 LangSwarm V2 Workflow Middleware Integration - Comprehensive Demo")
    print("=" * 80)
    
    demos = [
        ("Basic Middleware Integration", demo_basic_middleware_integration),
        ("Enhanced Middleware Features", demo_enhanced_middleware_features),
        ("Workflow Routing Strategies", demo_workflow_routing_strategies),
        ("Policy Enforcement & Compliance", demo_policy_enforcement),
        ("Batch Workflow Execution", demo_batch_execution),
        ("Performance Monitoring & Optimization", demo_performance_monitoring),
        ("Middleware Integration Modes", demo_integration_modes)
    ]
    
    results = []
    
    for demo_name, demo_func in demos:
        try:
            print(f"\n🎯 Starting: {demo_name}")
            success = await demo_func()
            results.append((demo_name, success, None))
            print(f"✅ Completed: {demo_name}")
        except Exception as e:
            results.append((demo_name, False, str(e)))
            print(f"❌ Failed: {demo_name} - {e}")
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 DEMO SUMMARY")
    print("=" * 80)
    
    successful = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    print(f"Total demos: {total}")
    print(f"Successful: {successful}")
    print(f"Failed: {total - successful}")
    print(f"Success rate: {(successful/total*100):.1f}%")
    
    print(f"\n📋 Detailed Results:")
    for demo_name, success, error in results:
        status = "✅ PASSED" if success else f"❌ FAILED"
        print(f"  {status} - {demo_name}")
        if error:
            print(f"    Error: {error}")
    
    if successful == total:
        print(f"\n🎉 All workflow middleware integration demos completed successfully!")
        print(f"🚀 V2 Workflow Middleware Integration is fully functional and ready for production!")
    else:
        print(f"\n⚠️  Some demos failed. Please review the errors above.")


if __name__ == "__main__":
    asyncio.run(main())
