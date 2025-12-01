#!/usr/bin/env python3
"""
LangSwarm Dependency Checker CLI

Provides commands to check dependency status and get installation guidance.
"""

import sys
from typing import Dict, List
import argparse

from langswarm.core.utils.optional_imports import optional_imports
from langswarm.core.agents.provider_registry import provider_registry
from langswarm.core.memory import MemoryFactory


def check_all_dependencies():
    """Check status of all optional dependencies."""
    print("🔍 LangSwarm Dependency Status Check")
    print("=" * 50)
    
    # Check providers
    print(provider_registry.get_provider_status_summary())
    print()
    
    # Check memory backends
    print("Memory Backends:")
    for backend in MemoryFactory.list_backends():
        info = MemoryFactory.get_backend_info(backend)
        status = "✅ Available" if info['available'] else "❌ Not available"
        print(f"  - {backend}: {status}")
    print()
    
    # Check overall optional features
    print(optional_imports.get_missing_dependencies_summary())


def check_specific_features(features: List[str]):
    """Check status of specific features."""
    print(f"🔍 Checking features: {', '.join(features)}")
    print("=" * 50)
    
    available_features = optional_imports.get_available_features()
    
    for feature in features:
        if feature in available_features:
            status = "✅ Available" if available_features[feature] else "❌ Not available"
            print(f"{feature}: {status}")
            
            if not available_features[feature]:
                group_info = optional_imports.dependency_groups.get(feature)
                if group_info:
                    print(f"   Install with: pip install langswarm[{group_info['extra']}]")
                    print(f"   Description: {group_info['description']}")
        else:
            print(f"{feature}: ❓ Unknown feature")
        print()


def list_all_features():
    """List all available feature groups."""
    print("📦 Available LangSwarm Feature Groups")
    print("=" * 50)
    
    features = optional_imports.get_available_features()
    
    # Group by category
    categories = {}
    for feature_name, available in features.items():
        group_info = optional_imports.dependency_groups.get(feature_name, {})
        extra = group_info.get('extra', 'other')
        
        if extra not in categories:
            categories[extra] = []
        
        categories[extra].append({
            'name': feature_name,
            'available': available,
            'description': group_info.get('description', 'No description')
        })
    
    for category, features_list in sorted(categories.items()):
        print(f"\n📁 {category.upper()}:")
        for feature in sorted(features_list, key=lambda x: x['name']):
            status = "✅" if feature['available'] else "❌"
            print(f"   {status} {feature['name']}: {feature['description']}")
        
        # Show install command for category
        available_count = sum(1 for f in features_list if f['available'])
        total_count = len(features_list)
        
        if available_count < total_count:
            print(f"   📥 Install all {category}: pip install langswarm[{category}]")


def get_minimal_installation():
    """Show minimal installation options."""
    print("⚡ Minimal LangSwarm Installation Options")
    print("=" * 50)
    
    print("🏃 Quick Start (minimal core):")
    print("   pip install langswarm")
    print("   • Core functionality only")
    print("   • SQLite memory backend")
    print("   • Local provider support")
    print()
    
    print("🎯 Essential Setup (recommended):")
    print("   pip install langswarm[essential]")
    print("   • OpenAI provider")
    print("   • Redis memory backend")
    print("   • FastAPI web framework")
    print()
    
    print("🏭 Production Setup:")
    print("   pip install langswarm[production]")
    print("   • Multiple AI providers")
    print("   • Cloud memory backends")
    print("   • Web frameworks")
    print()
    
    print("🎨 Full Installation:")
    print("   pip install langswarm[all]")
    print("   • All providers and backends")
    print("   • All integrations")
    print("   • Development tools")


def diagnose_installation():
    """Diagnose common installation issues."""
    print("🔧 LangSwarm Installation Diagnosis")
    print("=" * 50)
    
    # Check Python version
    python_version = sys.version_info
    print(f"Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    if python_version < (3, 8):
        print("❌ Python 3.8+ required")
        return
    else:
        print("✅ Python version compatible")
    
    print()
    
    # Check core imports
    try:
        import langswarm
        print("✅ LangSwarm core imported successfully")
        print(f"   Version: {getattr(langswarm, '__version__', 'unknown')}")
    except ImportError as e:
        print(f"❌ Failed to import LangSwarm: {e}")
        print("   Try: pip install langswarm")
        return
    
    print()
    
    # Check for common issues
    issues_found = 0
    
    # Check if any providers are available
    available_providers = provider_registry.list_available_providers()
    if not available_providers:
        print("⚠️  No AI providers available")
        print("   Install at least one: pip install langswarm[openai]")
        issues_found += 1
    else:
        print(f"✅ {len(available_providers)} AI provider(s) available: {', '.join(available_providers)}")
    
    # Check memory backends
    # Check memory backends
    available_backends = []
    for backend in MemoryFactory.list_backends():
        info = MemoryFactory.get_backend_info(backend)
        if info['available']:
            available_backends.append(backend)
            
    if len(available_backends) == 1 and 'sqlite' in available_backends:
        print("ℹ️  Only SQLite memory backend available")
        print("   For production, consider: pip install langswarm[redis]")
    else:
        print(f"✅ {len(available_backends)} memory backend(s) available: {', '.join(available_backends)}")
    
    print()
    
    if issues_found == 0:
        print("🎉 LangSwarm installation looks good!")
    else:
        print(f"🔧 Found {issues_found} issue(s) that may affect functionality")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="LangSwarm Dependency Checker",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Check all dependencies
    subparsers.add_parser('check', help='Check all dependency status')
    
    # Check specific features
    check_parser = subparsers.add_parser('features', help='Check specific features')
    check_parser.add_argument('feature_names', nargs='*', help='Feature names to check')
    
    # List all features
    subparsers.add_parser('list', help='List all available features')
    
    # Show minimal installation options
    subparsers.add_parser('minimal', help='Show minimal installation options')
    
    # Diagnose installation
    subparsers.add_parser('diagnose', help='Diagnose installation issues')
    
    args = parser.parse_args()
    
    if args.command == 'check':
        check_all_dependencies()
    elif args.command == 'features':
        if args.feature_names:
            check_specific_features(args.feature_names)
        else:
            list_all_features()
    elif args.command == 'list':
        list_all_features()
    elif args.command == 'minimal':
        get_minimal_installation()
    elif args.command == 'diagnose':
        diagnose_installation()
    else:
        parser.print_help()


if __name__ == '__main__':
    main()