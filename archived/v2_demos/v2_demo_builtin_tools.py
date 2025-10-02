#!/usr/bin/env python3
"""
LangSwarm V2 Built-in Tools Demonstration

This script demonstrates the built-in tools that ship with LangSwarm V2.
These tools provide essential functionality for common use cases.
"""

import asyncio
import json
from datetime import datetime


async def demo_system_status_tool():
    """Demonstrate the SystemStatusTool"""
    print("=" * 60)
    print("🔧 SYSTEM STATUS TOOL DEMO")
    print("=" * 60)
    
    try:
        from langswarm.v2.tools.builtin import SystemStatusTool
        
        tool = SystemStatusTool()
        print(f"✅ Created SystemStatusTool: {tool.metadata.name}")
        print(f"   Description: {tool.metadata.description}")
        print(f"   Version: {tool.metadata.version}")
        print()
        
        # Test health check
        print("🔍 Health Check:")
        health = await tool.health_check()
        print(json.dumps(health, indent=2))
        print()
        
        # Test system info
        print("💻 System Info:")
        sys_info = await tool.system_info()
        print(f"   Platform: {sys_info['system']['platform']}")
        print(f"   Python: {sys_info['python']['version'].split()[0]}")
        print(f"   Architecture: {sys_info['system']['architecture']}")
        print()
        
        # Test component status
        print("🔧 Component Status:")
        components = await tool.component_status()
        for component, status in components['components'].items():
            status_icon = "✅" if status.get('status') == 'active' else "❌"
            print(f"   {status_icon} {component}: {status.get('status', 'unknown')}")
        print()
        
    except Exception as e:
        print(f"❌ SystemStatusTool demo failed: {e}")
        import traceback
        traceback.print_exc()
    

async def demo_text_processor_tool():
    """Demonstrate the TextProcessorTool"""
    print("=" * 60)
    print("📝 TEXT PROCESSOR TOOL DEMO")
    print("=" * 60)
    
    try:
        from langswarm.v2.tools.builtin import TextProcessorTool
        
        tool = TextProcessorTool()
        print(f"✅ Created TextProcessorTool: {tool.metadata.name}")
        print()
        
        test_text = "Hello, LangSwarm V2! This is a test text for processing."
        
        # Test text transformation
        print("🔄 Text Transformation:")
        print(f"   Original: {test_text}")
        
        transformed = await tool.transform(test_text, ["upper", "reverse"])
        print(f"   Upper + Reverse: {transformed[:50]}...")
        print()
        
        # Test text analysis
        print("📊 Text Analysis:")
        analysis = await tool.analyze(test_text)
        print(f"   Length: {analysis['length']} characters")
        print(f"   Words: {analysis['words']}")
        print(f"   Lines: {analysis['lines']}")
        print(f"   Unique words: {analysis['unique_words']}")
        print()
        
        # Test encoding
        print("🔐 Encoding Demo:")
        encoded = await tool.encode(test_text, "base64")
        print(f"   Base64: {encoded[:30]}...")
        
        decoded = await tool.decode(encoded, "base64")
        print(f"   Decoded: {decoded}")
        print()
        
        # Test regex
        print("🔍 Regex Demo:")
        matches = await tool.regex_find(test_text, r'\b\w{4,}\b')  # Words with 4+ characters
        print(f"   Words 4+ chars: {matches[:5]}")
        print()
        
    except Exception as e:
        print(f"❌ TextProcessorTool demo failed: {e}")
        import traceback
        traceback.print_exc()


async def demo_file_operations_tool():
    """Demonstrate the FileOperationsTool"""
    print("=" * 60)
    print("📁 FILE OPERATIONS TOOL DEMO")
    print("=" * 60)
    
    try:
        from langswarm.v2.tools.builtin import FileOperationsTool
        import tempfile
        import os
        
        # Use temp directory for safe testing
        with tempfile.TemporaryDirectory() as temp_dir:
            tool = FileOperationsTool(base_path=temp_dir)
            print(f"✅ Created FileOperationsTool (base: {temp_dir})")
            print()
            
            # Test directory listing
            print("📂 Directory Listing:")
            contents = await tool.list_directory(".")
            print(f"   Initial contents: {len(contents)} items")
            print()
            
            # Test file writing
            print("✏️  File Writing:")
            test_content = f"LangSwarm V2 Test File\nCreated: {datetime.now()}\n"
            write_result = await tool.write_file("test.txt", test_content)
            print(f"   ✅ Created test.txt ({write_result['size']} bytes)")
            print()
            
            # Test file reading
            print("📖 File Reading:")
            read_content = await tool.read_file("test.txt")
            print(f"   Content: {read_content.strip()}")
            print()
            
            # Test file info
            print("ℹ️  File Info:")
            file_info = await tool.file_info("test.txt")
            print(f"   Size: {file_info['size']} bytes")
            print(f"   Type: {file_info['type']}")
            print(f"   Permissions: {file_info['permissions']}")
            print()
            
            # Test directory creation
            print("📁 Directory Creation:")
            dir_result = await tool.create_directory("subdir")
            print(f"   ✅ {dir_result['message']}")
            print()
            
            # Test file existence
            print("🔍 File Existence Check:")
            exists = await tool.file_exists("test.txt")
            not_exists = await tool.file_exists("nonexistent.txt")
            print(f"   test.txt exists: {exists}")
            print(f"   nonexistent.txt exists: {not_exists}")
            print()
        
    except Exception as e:
        print(f"❌ FileOperationsTool demo failed: {e}")
        import traceback
        traceback.print_exc()


async def demo_tool_inspector_tool():
    """Demonstrate the ToolInspectorTool"""
    print("=" * 60)
    print("🔍 TOOL INSPECTOR TOOL DEMO")
    print("=" * 60)
    
    try:
        from langswarm.v2.tools.builtin import ToolInspectorTool
        from langswarm.v2.tools import ToolRegistry
        
        tool = ToolInspectorTool()
        print(f"✅ Created ToolInspectorTool: {tool.metadata.name}")
        print()
        
        # Test tool listing (this will show limited info since we don't have a full registry)
        print("📋 Available Tools:")
        try:
            tools = await tool.list_tools(include_metadata=True)
            for tool_info in tools[:3]:  # Show first 3
                print(f"   📦 {tool_info.get('name', 'Unknown')}")
                if 'description' in tool_info:
                    print(f"      Description: {tool_info['description']}")
                if 'type' in tool_info:
                    print(f"      Type: {tool_info['type']}")
        except Exception as e:
            print(f"   ⚠️  Tool listing limited: {e}")
        print()
        
        # Test capability listing
        print("🔧 Available Capabilities:")
        capabilities = await tool.list_capabilities()
        for cap in capabilities[:5]:  # Show first 5
            if 'name' in cap:
                print(f"   ⚙️  {cap['name']}: {cap.get('description', 'No description')}")
        print()
        
        # Test documentation generation
        print("📚 Documentation Generation:")
        try:
            # Try to document some built-in tools
            docs = await tool.generate_docs(
                tool_names=["system_status", "text_processor"], 
                format="json"
            )
            if len(docs) > 200:
                print(f"   ✅ Generated documentation ({len(docs)} characters)")
                print(f"   Preview: {docs[:100]}...")
            else:
                print(f"   📄 Generated docs: {docs}")
        except Exception as e:
            print(f"   ⚠️  Documentation generation limited: {e}")
        print()
        
    except Exception as e:
        print(f"❌ ToolInspectorTool demo failed: {e}")
        import traceback
        traceback.print_exc()


async def demo_web_request_tool():
    """Demonstrate the WebRequestTool (if requests is available)"""
    print("=" * 60)
    print("🌐 WEB REQUEST TOOL DEMO")
    print("=" * 60)
    
    try:
        from langswarm.v2.tools.builtin import WebRequestTool
        
        # Use public test APIs that are safe
        tool = WebRequestTool(
            allowed_domains=["httpbin.org", "jsonplaceholder.typicode.com"],
            timeout=10
        )
        print(f"✅ Created WebRequestTool: {tool.metadata.name}")
        print()
        
        # Test GET request to a safe public API
        print("🔍 GET Request Test:")
        try:
            response = await tool.get("https://httpbin.org/get?test=langswarm")
            print(f"   Status: {response['status_code']}")
            print(f"   Response size: {response.get('size_bytes', 0)} bytes")
            if 'json' in response:
                print(f"   Test param received: {response['json'].get('args', {}).get('test', 'none')}")
        except Exception as e:
            print(f"   ⚠️  GET request failed (might be network/dependency issue): {e}")
        print()
        
        # Test POST request
        print("📤 POST Request Test:")
        try:
            post_data = {"message": "Hello from LangSwarm V2", "tool": "web_request"}
            response = await tool.post("https://httpbin.org/post", data=post_data)
            print(f"   Status: {response['status_code']}")
            if 'json' in response:
                posted_data = response['json'].get('json', {})
                print(f"   Posted message: {posted_data.get('message', 'none')}")
        except Exception as e:
            print(f"   ⚠️  POST request failed (might be network/dependency issue): {e}")
        print()
        
    except ImportError:
        print("⚠️  WebRequestTool requires 'requests' library")
        print("   Install with: pip install requests")
    except Exception as e:
        print(f"❌ WebRequestTool demo failed: {e}")
        import traceback
        traceback.print_exc()


async def demo_mcp_compatibility():
    """Demonstrate MCP compatibility of built-in tools"""
    print("=" * 60)
    print("🔌 MCP COMPATIBILITY DEMO")
    print("=" * 60)
    
    try:
        from langswarm.v2.tools.builtin import SystemStatusTool, TextProcessorTool
        
        # Test MCP run method
        print("🔄 MCP Run Method Tests:")
        
        # SystemStatusTool via run method (await the result since we're in an async context)
        system_tool = SystemStatusTool()
        health_task = system_tool.run({"method": "health_check"})
        if asyncio.iscoroutine(health_task) or hasattr(health_task, '__await__'):
            health = await health_task
        else:
            health = health_task
        print(f"   ✅ SystemStatus.run(): {health.get('status', 'unknown')}")
        
        # TextProcessorTool via run method
        text_tool = TextProcessorTool()
        analysis_task = text_tool.run({
            "method": "analyze", 
            "text": "MCP compatibility test"
        })
        if asyncio.iscoroutine(analysis_task) or hasattr(analysis_task, '__await__'):
            analysis = await analysis_task
        else:
            analysis = analysis_task
        print(f"   ✅ TextProcessor.run(): {analysis.get('words', 0)} words analyzed")
        
        # Test with kwargs style
        transform_task = text_tool.run(
            method="transform",
            text="hello world",
            operations=["upper", "reverse"]
        )
        if asyncio.iscoroutine(transform_task) or hasattr(transform_task, '__await__'):
            transform_result = await transform_task
        else:
            transform_result = transform_task
        print(f"   ✅ TextProcessor.run() with kwargs: {transform_result}")
        
        print()
        
    except Exception as e:
        print(f"❌ MCP compatibility demo failed: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Run all built-in tool demonstrations"""
    print("🚀 LangSwarm V2 Built-in Tools Demonstration")
    print(f"⏰ Started at: {datetime.now()}")
    print()
    
    # Run all demos
    await demo_system_status_tool()
    await demo_text_processor_tool() 
    await demo_file_operations_tool()
    await demo_tool_inspector_tool()
    await demo_web_request_tool()
    await demo_mcp_compatibility()
    
    print("=" * 60)
    print("✅ Built-in Tools Demonstration Complete!")
    print("=" * 60)
    print()
    print("🎯 Summary:")
    print("   • SystemStatusTool: System health and diagnostics")
    print("   • TextProcessorTool: Text manipulation and analysis")
    print("   • FileOperationsTool: Safe file operations")
    print("   • ToolInspectorTool: Tool introspection and documentation")
    print("   • WebRequestTool: HTTP requests with security controls")
    print()
    print("All tools support both async execution and MCP compatibility!")


if __name__ == "__main__":
    asyncio.run(main())
