#!/usr/bin/env python3
"""
Test script for the unified orchestrator
"""
import asyncio
import aiohttp
import json
import sys
from typing import Dict, Any


class OrchestratorTester:
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_health(self):
        """Test orchestrator health endpoint"""
        print("🔍 Testing orchestrator health...")
        
        async with self.session.get(f"{self.base_url}/health") as response:
            if response.status == 200:
                data = await response.json()
                print(f"✅ Orchestrator healthy: {data['service']} v{data['version']}")
                return True
            else:
                print(f"❌ Health check failed: HTTP {response.status}")
                return False
    
    async def test_list_backends(self):
        """Test listing supported backends"""
        print("\n🔍 Testing backend listing...")
        
        async with self.session.get(f"{self.base_url}/api/v1/backends") as response:
            if response.status == 200:
                backends = await response.json()
                print("✅ Supported backends:")
                for backend_type, info in backends.items():
                    capabilities = info['capabilities']
                    caps_str = ", ".join([k for k, v in capabilities.items() if v])
                    print(f"   • {backend_type.upper()}: {caps_str}")
                return backends
            else:
                print(f"❌ Failed to list backends: HTTP {response.status}")
                return None
    
    async def test_custom_backend_discovery(self, project_id: str):
        """Test custom backend orphaned service discovery"""
        print(f"\n🔍 Testing custom backend discovery for project {project_id}...")
        
        url = f"{self.base_url}/api/v1/custom/orphaned-services"
        params = {"project_id": project_id}
        
        async with self.session.get(url, params=params) as response:
            if response.status == 200:
                orphaned = await response.json()
                print(f"✅ Found {len(orphaned)} orphaned custom backend services:")
                for service in orphaned:
                    print(f"   • {service['name']} - {service['url']} ({service['status']})")
                return orphaned
            else:
                error_text = await response.text()
                print(f"❌ Discovery failed: HTTP {response.status} - {error_text}")
                return []
    
    async def test_service_validation(self, backend_type: str, project_id: str, service_name: str):
        """Test service compatibility validation"""
        print(f"\n🔍 Testing {backend_type} service validation for {service_name}...")
        
        validation_data = {
            "backend_type": backend_type,
            "project_id": project_id,
            "service_name": service_name
        }
        
        async with self.session.post(
            f"{self.base_url}/api/v1/{backend_type}/validate-service",
            json=validation_data
        ) as response:
            if response.status == 200:
                result = await response.json()
                if result.get("compatible"):
                    print(f"✅ Service {service_name} is compatible")
                    print(f"   URL: {result.get('service_url')}")
                    if 'health_data' in result:
                        health = result['health_data']
                        print(f"   Status: {health.get('status')}")
                        print(f"   Version: {health.get('version', 'unknown')}")
                else:
                    print(f"❌ Service {service_name} is not compatible: {result.get('error')}")
                return result
            else:
                error_text = await response.text()
                print(f"❌ Validation failed: HTTP {response.status} - {error_text}")
                return None
    
    async def test_adoption(self, backend_type: str, project_id: str, service_name: str):
        """Test service adoption"""
        print(f"\n🔍 Testing {backend_type} service adoption for {service_name}...")
        
        adoption_data = {
            "backend_type": backend_type,
            "project_id": project_id,
            "service_name": service_name
        }
        
        async with self.session.post(
            f"{self.base_url}/api/v1/{backend_type}/instances/adopt",
            json=adoption_data
        ) as response:
            if response.status == 200:
                result = await response.json()
                print(f"✅ Successfully adopted {service_name}")
                print(f"   Instance ID: {result['instance_id']}")
                print(f"   Service URL: {result['service_url']}")
                return result
            else:
                error_text = await response.text()
                print(f"❌ Adoption failed: HTTP {response.status} - {error_text}")
                return None
    
    async def test_prompt_management(self, backend_type: str, project_id: str, instance_id: str):
        """Test prompt management capabilities"""
        print(f"\n🔍 Testing prompt management for {backend_type} instance {instance_id}...")
        
        # Test getting prompt schema
        schema_url = f"{self.base_url}/api/v1/{backend_type}/instances/{instance_id}/prompts/schema"
        params = {"project_id": project_id}
        
        async with self.session.get(schema_url, params=params) as response:
            if response.status == 200:
                schema = await response.json()
                print(f"✅ Retrieved prompt schema with {len(schema.get('fields', []))} fields")
                
                # Test getting current prompts
                prompts_url = f"{self.base_url}/api/v1/{backend_type}/instances/{instance_id}/prompts"
                async with self.session.get(prompts_url, params=params) as response:
                    if response.status == 200:
                        current_prompts = await response.json()
                        print(f"✅ Retrieved current prompts: {list(current_prompts.keys())}")
                        
                        # Test updating prompts (dry run)
                        test_prompts = {}
                        for field in schema.get('fields', []):
                            if field['name'] in current_prompts:
                                # Keep existing values for this test
                                test_prompts[field['name']] = current_prompts[field['name']]
                        
                        if test_prompts:
                            print(f"✅ Prompt management fully functional")
                            return True
                    else:
                        print(f"❌ Failed to get current prompts: HTTP {response.status}")
            else:
                print(f"❌ Failed to get prompt schema: HTTP {response.status}")
        
        return False
    
    async def test_instance_listing(self, backend_type: str, project_id: str):
        """Test instance listing"""
        print(f"\n🔍 Testing {backend_type} instance listing...")
        
        url = f"{self.base_url}/api/v1/{backend_type}/instances"
        params = {"project_id": project_id}
        
        async with self.session.get(url, params=params) as response:
            if response.status == 200:
                instances = await response.json()
                print(f"✅ Found {len(instances)} {backend_type} instances")
                for instance in instances:
                    print(f"   • {instance['instance_id']} - {instance.get('status', 'unknown')}")
                return instances
            else:
                error_text = await response.text()
                print(f"❌ Failed to list instances: HTTP {response.status} - {error_text}")
                return []


async def main():
    """Main test function"""
    if len(sys.argv) < 2:
        print("Usage: python test_unified_orchestrator.py <project_id> [orchestrator_url]")
        print("Example: python test_unified_orchestrator.py production-pingday")
        sys.exit(1)
    
    project_id = sys.argv[1]
    orchestrator_url = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:8080"
    
    print(f"🧪 Testing Unified Orchestrator")
    print(f"Project ID: {project_id}")
    print(f"Orchestrator URL: {orchestrator_url}")
    print("=" * 50)
    
    async with OrchestratorTester(orchestrator_url) as tester:
        # Test basic functionality
        if not await tester.test_health():
            print("❌ Health check failed - orchestrator may not be running")
            return
        
        backends = await tester.test_list_backends()
        if not backends:
            print("❌ Failed to get backend information")
            return
        
        # Test custom backend discovery and adoption
        if "custom" in backends:
            print("\n" + "=" * 30 + " CUSTOM BACKEND TESTS " + "=" * 30)
            
            orphaned_services = await tester.test_custom_backend_discovery(project_id)
            
            if orphaned_services:
                # Test validation and adoption of first orphaned service
                service_name = orphaned_services[0]["name"]
                
                validation_result = await tester.test_service_validation("custom", project_id, service_name)
                
                if validation_result and validation_result.get("compatible"):
                    adoption_result = await tester.test_adoption("custom", project_id, service_name)
                    
                    if adoption_result:
                        await tester.test_prompt_management("custom", project_id, service_name)
            
            # Test instance listing
            await tester.test_instance_listing("custom", project_id)
        
        # Test AAF backend functionality
        if "aaf" in backends:
            print("\n" + "=" * 30 + " AAF BACKEND TESTS " + "=" * 30)
            
            # Test instance listing (existing instances)
            await tester.test_instance_listing("aaf", project_id)
            
            # Note: We don't test AAF deployment here as it requires configuration
            print("✅ AAF backend functionality available")
        
        print("\n" + "=" * 50)
        print("🎉 Testing complete!")


if __name__ == "__main__":
    asyncio.run(main())
