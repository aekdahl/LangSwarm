"""
Unit tests for LangSwarm V2 middleware pipeline
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock

from langswarm.v2.core.middleware.pipeline import Pipeline, PipelineBuilder, create_default_pipeline
from langswarm.v2.core.middleware.context import RequestContext, ResponseContext
from langswarm.v2.core.middleware.interfaces import RequestType, ResponseStatus
from langswarm.v2.core.middleware.interceptors.base import BaseInterceptor, PassthroughInterceptor, TerminatingInterceptor


class TestPipeline:
    """Test Pipeline class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.pipeline = Pipeline()
    
    def test_pipeline_initialization(self):
        """Test pipeline initialization"""
        assert self.pipeline.interceptor_count == 0
        assert len(self.pipeline.get_interceptors()) == 0
    
    def test_add_interceptor(self):
        """Test adding interceptors to pipeline"""
        interceptor = PassthroughInterceptor("test", priority=100)
        
        result = self.pipeline.add_interceptor(interceptor)
        
        assert result is self.pipeline  # Should return self for chaining
        assert self.pipeline.interceptor_count == 1
        assert self.pipeline.has_interceptor("test")
        assert self.pipeline.get_interceptor("test") is interceptor
    
    def test_interceptor_ordering_by_priority(self):
        """Test that interceptors are ordered by priority"""
        interceptor1 = PassthroughInterceptor("high", priority=10)
        interceptor2 = PassthroughInterceptor("low", priority=100)
        interceptor3 = PassthroughInterceptor("medium", priority=50)
        
        self.pipeline.add_interceptor(interceptor2)
        self.pipeline.add_interceptor(interceptor1)
        self.pipeline.add_interceptor(interceptor3)
        
        interceptors = self.pipeline.get_interceptors()
        assert interceptors[0].name == "high"
        assert interceptors[1].name == "medium"
        assert interceptors[2].name == "low"
    
    def test_remove_interceptor(self):
        """Test removing interceptors from pipeline"""
        interceptor = PassthroughInterceptor("test")
        
        self.pipeline.add_interceptor(interceptor)
        assert self.pipeline.has_interceptor("test")
        
        result = self.pipeline.remove_interceptor("test")
        assert result is self.pipeline  # Should return self for chaining
        assert not self.pipeline.has_interceptor("test")
        assert self.pipeline.interceptor_count == 0
    
    def test_remove_nonexistent_interceptor(self):
        """Test removing non-existent interceptor"""
        # Should not raise exception
        result = self.pipeline.remove_interceptor("nonexistent")
        assert result is self.pipeline
    
    @pytest.mark.asyncio
    async def test_process_empty_pipeline(self):
        """Test processing request with empty pipeline"""
        context = RequestContext(action_id="test", method="test_method")
        
        response = await self.pipeline.process(context)
        
        assert response.request_id == context.request_id
        assert response.is_error()  # Empty pipeline should return NOT_FOUND
        assert response.status == ResponseStatus.NOT_FOUND
    
    @pytest.mark.asyncio
    async def test_process_with_passthrough_interceptor(self):
        """Test processing with passthrough interceptor"""
        interceptor = PassthroughInterceptor("test")
        self.pipeline.add_interceptor(interceptor)
        
        context = RequestContext(action_id="test", method="test_method")
        
        response = await self.pipeline.process(context)
        
        assert response.request_id == context.request_id
        assert response.is_success()
    
    @pytest.mark.asyncio
    async def test_process_with_terminating_interceptor(self):
        """Test processing with terminating interceptor"""
        test_result = {"message": "test result"}
        interceptor = TerminatingInterceptor(test_result, "test")
        self.pipeline.add_interceptor(interceptor)
        
        context = RequestContext(action_id="test", method="test_method")
        
        response = await self.pipeline.process(context)
        
        assert response.request_id == context.request_id
        assert response.is_success()
        assert response.result == test_result
    
    @pytest.mark.asyncio
    async def test_process_interceptor_chain(self):
        """Test processing through multiple interceptors"""
        # Create interceptors that modify context metadata
        class MetadataInterceptor(BaseInterceptor):
            def __init__(self, name, value, priority=100):
                super().__init__(name=name, priority=priority)
                self.value = value
            
            async def _process(self, context, next_interceptor):
                enhanced_context = context.with_metadata(**{self.name: self.value})
                return await next_interceptor(enhanced_context)
        
        interceptor1 = MetadataInterceptor("first", "value1", priority=10)
        interceptor2 = MetadataInterceptor("second", "value2", priority=20)
        terminator = TerminatingInterceptor("final", "terminator", priority=30)
        
        self.pipeline.add_interceptor(interceptor2)
        self.pipeline.add_interceptor(terminator)
        self.pipeline.add_interceptor(interceptor1)
        
        context = RequestContext(action_id="test", method="test_method")
        
        response = await self.pipeline.process(context)
        
        assert response.is_success()
        assert response.result == "final"
        # Check that timing metadata from all interceptors is preserved
        assert "first_processing_time" in response.metadata
        assert "second_processing_time" in response.metadata
        assert "terminator_processing_time" in response.metadata
        assert "interceptor_chain" in response.metadata
        assert response.metadata["interceptor_chain"] == ["first", "second", "terminator"]
    
    @pytest.mark.asyncio
    async def test_process_interceptor_error_handling(self):
        """Test error handling in interceptor chain"""
        class ErrorInterceptor(BaseInterceptor):
            async def _process(self, context, next_interceptor):
                raise ValueError("Test error")
        
        error_interceptor = ErrorInterceptor("error")
        self.pipeline.add_interceptor(error_interceptor)
        
        context = RequestContext(action_id="test", method="test_method")
        
        response = await self.pipeline.process(context)
        
        assert response.is_error()
        assert response.status == ResponseStatus.BAD_REQUEST  # ValueError maps to BAD_REQUEST
        assert response.error is not None
    
    def test_clone_pipeline(self):
        """Test cloning pipeline"""
        interceptor1 = PassthroughInterceptor("test1")
        interceptor2 = PassthroughInterceptor("test2")
        
        self.pipeline.add_interceptor(interceptor1)
        self.pipeline.add_interceptor(interceptor2)
        
        cloned = self.pipeline.clone()
        
        assert cloned is not self.pipeline
        assert cloned.interceptor_count == self.pipeline.interceptor_count
        assert cloned.has_interceptor("test1")
        assert cloned.has_interceptor("test2")
    
    def test_clear_pipeline(self):
        """Test clearing pipeline"""
        interceptor = PassthroughInterceptor("test")
        self.pipeline.add_interceptor(interceptor)
        
        assert self.pipeline.interceptor_count == 1
        
        result = self.pipeline.clear()
        
        assert result is self.pipeline
        assert self.pipeline.interceptor_count == 0
        assert not self.pipeline.has_interceptor("test")


class TestPipelineBuilder:
    """Test PipelineBuilder class"""
    
    def test_builder_initialization(self):
        """Test builder initialization"""
        builder = PipelineBuilder()
        assert builder is not None
    
    def test_add_interceptor_chaining(self):
        """Test method chaining in builder"""
        builder = PipelineBuilder()
        
        result = builder.add_interceptor(PassthroughInterceptor("test"))
        
        assert result is builder  # Should return self for chaining
    
    def test_build_pipeline(self):
        """Test building pipeline"""
        interceptor = PassthroughInterceptor("test")
        
        pipeline = (PipelineBuilder()
                   .add_interceptor(interceptor)
                   .build())
        
        assert isinstance(pipeline, Pipeline)
        assert pipeline.has_interceptor("test")
        assert pipeline.interceptor_count == 1
    
    def test_create_default_pipeline(self):
        """Test creating default pipeline"""
        pipeline = PipelineBuilder.create_default()
        
        assert isinstance(pipeline, Pipeline)
        assert pipeline.interceptor_count > 0
        
        # Should have standard interceptors
        interceptor_names = [i.name for i in pipeline.get_interceptors()]
        assert "error" in interceptor_names
        assert "observability" in interceptor_names
        assert "routing" in interceptor_names
        assert "validation" in interceptor_names
        assert "execution" in interceptor_names
    
    def test_create_minimal_pipeline(self):
        """Test creating minimal pipeline"""
        pipeline = PipelineBuilder.create_minimal()
        
        assert isinstance(pipeline, Pipeline)
        assert pipeline.interceptor_count == 2  # routing + execution
        
        interceptor_names = [i.name for i in pipeline.get_interceptors()]
        assert "routing" in interceptor_names
        assert "execution" in interceptor_names
    
    def test_fluent_builder_interface(self):
        """Test fluent builder interface"""
        pipeline = (PipelineBuilder()
                   .add_routing(priority=100)
                   .add_validation(priority=200)
                   .add_execution(priority=500)
                   .with_config(timeout=30)
                   .build())
        
        assert pipeline.interceptor_count == 3
        assert pipeline.has_interceptor("routing")
        assert pipeline.has_interceptor("validation")
        assert pipeline.has_interceptor("execution")


class TestConvenienceFunctions:
    """Test convenience functions"""
    
    def test_create_default_pipeline(self):
        """Test create_default_pipeline function"""
        pipeline = create_default_pipeline()
        
        assert isinstance(pipeline, Pipeline)
        assert pipeline.interceptor_count > 0


@pytest.mark.asyncio
class TestAsyncPipelineExecution:
    """Test async execution aspects of pipeline"""
    
    async def test_async_interceptor_execution(self):
        """Test that async interceptors work correctly"""
        class AsyncInterceptor(BaseInterceptor):
            async def _process(self, context, next_interceptor):
                # Simulate async work
                await asyncio.sleep(0.01)
                return await next_interceptor(context)
        
        pipeline = Pipeline()
        pipeline.add_interceptor(AsyncInterceptor("async"))
        pipeline.add_interceptor(TerminatingInterceptor("result", "terminator"))
        
        context = RequestContext(action_id="test", method="test_method")
        
        response = await pipeline.process(context)
        
        assert response.is_success()
        assert response.result == "result"
    
    async def test_concurrent_pipeline_processing(self):
        """Test concurrent processing of multiple requests"""
        pipeline = Pipeline()
        pipeline.add_interceptor(TerminatingInterceptor("result", "terminator"))
        
        contexts = [
            RequestContext(action_id=f"test_{i}", method="test_method")
            for i in range(5)
        ]
        
        # Process all contexts concurrently
        responses = await asyncio.gather(*[
            pipeline.process(context) for context in contexts
        ])
        
        assert len(responses) == 5
        for response in responses:
            assert response.is_success()
            assert response.result == "result"
