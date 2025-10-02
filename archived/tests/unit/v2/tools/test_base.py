"""
Unit tests for LangSwarm V2 base tool classes
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock

from langswarm.v2.tools.base import (
    BaseTool, 
    ToolMetadata, 
    ToolResult, 
    ToolExecution,
    create_tool_metadata,
    create_method_schema
)
from langswarm.v2.tools.interfaces import ToolType, ToolCapability, ToolSchema


class TestToolResult:
    """Test ToolResult class"""
    
    def test_success_result_creation(self):
        """Test creating successful result"""
        result = ToolResult.success_result("test data", test_meta="value")
        
        assert result.success is True
        assert result.data == "test data"
        assert result.error is None
        assert result.metadata["test_meta"] == "value"
    
    def test_error_result_creation(self):
        """Test creating error result"""
        result = ToolResult.error_result("test error", error_code=500)
        
        assert result.success is False
        assert result.data is None
        assert result.error == "test error"
        assert result.metadata["error_code"] == 500
    
    def test_to_dict_conversion(self):
        """Test converting result to dictionary"""
        result = ToolResult.success_result("test", meta="value")
        result_dict = result.to_dict()
        
        assert result_dict["success"] is True
        assert result_dict["data"] == "test"
        assert result_dict["metadata"]["meta"] == "value"
        assert "timestamp" in result_dict
    
    def test_to_json_conversion(self):
        """Test converting result to JSON"""
        result = ToolResult.success_result("test")
        json_str = result.to_json()
        
        assert isinstance(json_str, str)
        assert '"success": true' in json_str
        assert '"data": "test"' in json_str


class TestToolMetadata:
    """Test ToolMetadata class"""
    
    def test_metadata_creation(self):
        """Test creating tool metadata"""
        metadata = ToolMetadata(
            id="test_tool",
            name="Test Tool",
            description="A test tool",
            tool_type=ToolType.UTILITY,
            capabilities=[ToolCapability.READ],
            tags=["test"]
        )
        
        assert metadata.id == "test_tool"
        assert metadata.name == "Test Tool"
        assert metadata.description == "A test tool"
        assert metadata.tool_type == ToolType.UTILITY
        assert ToolCapability.READ in metadata.capabilities
        assert "test" in metadata.tags
    
    def test_add_method(self):
        """Test adding method to metadata"""
        metadata = ToolMetadata("test", "Test", "Description")
        
        schema = ToolSchema(
            name="test_method",
            description="Test method",
            parameters={"param": {"type": "string"}},
            returns={"type": "string"}
        )
        
        metadata.add_method(schema)
        
        assert "test_method" in metadata.methods
        assert metadata.methods["test_method"] == schema
    
    def test_add_capability(self):
        """Test adding capability"""
        metadata = ToolMetadata("test", "Test", "Description")
        
        metadata.add_capability(ToolCapability.WRITE)
        
        assert ToolCapability.WRITE in metadata.capabilities
    
    def test_add_tag(self):
        """Test adding tag"""
        metadata = ToolMetadata("test", "Test", "Description")
        
        metadata.add_tag("new_tag")
        
        assert "new_tag" in metadata.tags
    
    def test_to_dict_conversion(self):
        """Test converting metadata to dictionary"""
        metadata = ToolMetadata(
            id="test",
            name="Test",
            description="Description",
            capabilities=[ToolCapability.READ]
        )
        
        metadata_dict = metadata.to_dict()
        
        assert metadata_dict["id"] == "test"
        assert metadata_dict["name"] == "Test"
        assert metadata_dict["capabilities"] == ["read"]


class TestToolExecution:
    """Test ToolExecution class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.mock_tool = Mock()
        self.mock_tool.metadata = ToolMetadata("test", "Test", "Description")
        self.execution = ToolExecution(self.mock_tool)
    
    @pytest.mark.asyncio
    async def test_execute_success(self):
        """Test successful execution"""
        # Create a real method that returns a value
        def test_method(**kwargs):
            return "success"
        self.mock_tool.test_method = test_method
        
        result = await self.execution.execute("test_method", {"param": "value"})
        
        assert isinstance(result, ToolResult)
        assert result.success is True
        assert result.data == "success"
    
    @pytest.mark.asyncio
    async def test_execute_async_method(self):
        """Test executing async method"""
        # Mock async tool method
        async def async_method(**kwargs):
            return "async_success"
        
        self.mock_tool.async_method = async_method
        
        result = await self.execution.execute("async_method", {"param": "value"})
        
        assert result.success is True
        assert result.data == "async_success"
    
    @pytest.mark.asyncio
    async def test_execute_nonexistent_method(self):
        """Test executing non-existent method"""
        result = await self.execution.execute("nonexistent", {})
        
        assert result.success is False
        assert "not found" in result.error.lower()
    
    @pytest.mark.asyncio
    async def test_execute_method_error(self):
        """Test method execution error"""
        def error_method(**kwargs):
            raise ValueError("Test error")
        
        self.mock_tool.error_method = error_method
        
        result = await self.execution.execute("error_method", {})
        
        assert result.success is False
        assert "Test error" in result.error
    
    def test_execute_sync(self):
        """Test synchronous execution"""
        def sync_method(**kwargs):
            return "sync_result"
        self.mock_tool.sync_method = sync_method
        
        result = self.execution.execute_sync("sync_method", {})
        
        assert result.success is True
        assert result.data == "sync_result"
    
    @pytest.mark.asyncio
    async def test_execute_stream(self):
        """Test streaming execution"""
        # Mock streaming method
        async def stream_method(**kwargs):
            for i in range(3):
                yield f"item_{i}"
        
        self.mock_tool.test_method_stream = stream_method
        
        results = []
        async for item in self.execution.execute_stream("test_method", {}):
            results.append(item)
        
        assert len(results) == 3
        assert results[0] == "item_0"
    
    def test_validate_method_exists(self):
        """Test method validation when method exists"""
        # Create a real method, not a Mock
        def real_method(**kwargs):
            return "result"
        self.mock_tool.valid_method = real_method
        
        is_valid = self.execution.validate_method("valid_method", {})
        
        assert is_valid is True
    
    def test_validate_method_not_exists(self):
        """Test method validation when method doesn't exist"""
        is_valid = self.execution.validate_method("nonexistent", {})
        
        assert is_valid is False
    
    def test_get_statistics(self):
        """Test getting execution statistics"""
        stats = self.execution.get_statistics()
        
        assert "total_calls" in stats
        assert "successful_calls" in stats
        assert "failed_calls" in stats
        assert "success_rate" in stats


class TestBaseTool:
    """Test BaseTool class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.tool = BaseTool(
            tool_id="test_tool",
            name="Test Tool",
            description="A test tool",
            capabilities=[ToolCapability.READ, ToolCapability.EXECUTE]
        )
    
    def test_tool_initialization(self):
        """Test tool initialization"""
        assert self.tool.metadata.id == "test_tool"
        assert self.tool.metadata.name == "Test Tool"
        assert self.tool.metadata.description == "A test tool"
        assert ToolCapability.READ in self.tool.metadata.capabilities
        assert ToolCapability.EXECUTE in self.tool.metadata.capabilities
    
    @pytest.mark.asyncio
    async def test_initialize_tool(self):
        """Test tool initialization"""
        config = {"setting": "value"}
        
        result = await self.tool.initialize(config)
        
        assert result is True
        assert self.tool.config["setting"] == "value"
    
    @pytest.mark.asyncio
    async def test_cleanup_tool(self):
        """Test tool cleanup"""
        result = await self.tool.cleanup()
        
        assert result is True
    
    def test_health_check(self):
        """Test health check"""
        health = self.tool.health_check()
        
        assert health["tool_id"] == "test_tool"
        assert "status" in health
        assert "timestamp" in health
    
    def test_get_schema(self):
        """Test getting tool schema"""
        # Add a method first
        self.tool.add_method(
            "test_method",
            "Test method",
            {"param": {"type": "string"}},
            {"type": "string"}
        )
        
        schema = self.tool.get_schema()
        
        assert schema["id"] == "test_tool"
        assert schema["name"] == "Test Tool"
        assert "test_method" in schema["methods"]
    
    def test_add_method(self):
        """Test adding method to tool"""
        self.tool.add_method(
            "new_method",
            "New method",
            {"param": {"type": "string"}},
            {"type": "string"},
            required=["param"]
        )
        
        assert "new_method" in self.tool.metadata.methods
        method_schema = self.tool.metadata.methods["new_method"]
        assert method_schema.name == "new_method"
        assert "param" in method_schema.required
    
    def test_add_capability(self):
        """Test adding capability to tool"""
        initial_count = len(self.tool.metadata.capabilities)
        
        self.tool.add_capability(ToolCapability.WRITE)
        
        assert len(self.tool.metadata.capabilities) == initial_count + 1
        assert ToolCapability.WRITE in self.tool.metadata.capabilities
    
    def test_add_tag(self):
        """Test adding tag to tool"""
        self.tool.add_tag("new_tag")
        
        assert "new_tag" in self.tool.metadata.tags
    
    def test_run_not_implemented(self):
        """Test that run method raises NotImplementedError"""
        with pytest.raises(NotImplementedError):
            self.tool.run()
    
    def test_use_alias(self):
        """Test that use method calls run method"""
        with pytest.raises(NotImplementedError):
            self.tool.use()


class TestUtilityFunctions:
    """Test utility functions"""
    
    def test_create_tool_metadata(self):
        """Test creating tool metadata with utility function"""
        metadata = create_tool_metadata(
            "util_tool",
            "Utility Tool",
            "A utility tool",
            tool_type=ToolType.UTILITY
        )
        
        assert isinstance(metadata, ToolMetadata)
        assert metadata.id == "util_tool"
        assert metadata.tool_type == ToolType.UTILITY
    
    def test_create_method_schema(self):
        """Test creating method schema with utility function"""
        schema = create_method_schema(
            "util_method",
            "Utility method",
            {"param": {"type": "string"}},
            required=["param"]
        )
        
        assert isinstance(schema, ToolSchema)
        assert schema.name == "util_method"
        assert "param" in schema.required


class ConcreteTestTool(BaseTool):
    """Concrete tool implementation for testing"""
    
    def __init__(self):
        super().__init__(
            tool_id="concrete_test",
            name="Concrete Test Tool",
            description="A concrete test tool"
        )
        
        # Add test methods
        self.add_method(
            "echo",
            "Echo input back",
            {"message": {"type": "string"}},
            {"type": "string"},
            required=["message"]
        )
    
    def run(self, input_data=None, **kwargs):
        """Implementation of run method"""
        if isinstance(input_data, dict) and "message" in input_data:
            return input_data["message"]
        elif "message" in kwargs:
            return kwargs["message"]
        else:
            return "No message provided"


class TestConcreteBaseTool:
    """Test concrete implementation of BaseTool"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.tool = ConcreteTestTool()
    
    def test_concrete_tool_run(self):
        """Test concrete tool run method"""
        result = self.tool.run({"message": "Hello, World!"})
        assert result == "Hello, World!"
        
        result = self.tool.run(message="Hello via kwargs")
        assert result == "Hello via kwargs"
        
        result = self.tool.run()
        assert result == "No message provided"
    
    @pytest.mark.asyncio
    async def test_concrete_tool_execution(self):
        """Test concrete tool execution through execution interface"""
        # The execution interface will call run with parameters as a dict
        result = await self.tool.execution.execute("echo", {"message": "Test message"})
        
        assert result.success is True
        # The run method receives the parameters dict, so it should extract the message
        assert result.data == "Test message"
