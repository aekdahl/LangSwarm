"""
End-to-End Tests for LangSwarm Memory Systems

Tests real memory backends, embedding providers, and vector search
with actual cloud services and databases.
"""

import asyncio
import random
import string
from typing import Dict, Any, List
from ..framework.base import BaseE2ETest


class SQLiteMemoryTest(BaseE2ETest):
    """Test SQLite memory backend with real data."""
    
    @property
    def test_name(self) -> str:
        return "SQLite Memory Backend"
    
    @property
    def required_providers(self) -> List[str]:
        return []
    
    @property
    def required_resources(self) -> List[str]:
        return []
    
    def estimated_cost(self) -> float:
        return 0.0  # No API costs
    
    async def run_test(self) -> Dict[str, Any]:
        """Test SQLite memory operations."""
        self.logger.info("Testing SQLite memory backend")
        
        try:
            # Import memory components
            from langswarm.core.session import create_session
            
            # Create session with SQLite memory
            session = create_session(
                session_id=f"test_session_{random.randint(1000, 9999)}",
                memory_backend="sqlite",
                storage_backend="sqlite"
            )
            
            # Test data
            test_documents = [
                "LangSwarm is a multi-agent orchestration framework for AI applications.",
                "Vector databases enable efficient similarity search for AI embeddings.",
                "Machine learning models require careful training and validation processes.",
                "Natural language processing has advanced significantly with transformer models.",
                "Distributed systems must handle failures gracefully and maintain consistency."
            ]
            
            # Store documents
            stored_count = 0
            for i, doc in enumerate(test_documents):
                try:
                    await session.memory.store(
                        key=f"doc_{i}",
                        content=doc,
                        metadata={"type": "test_document", "index": i}
                    )
                    stored_count += 1
                except Exception as e:
                    self.logger.error(f"Failed to store document {i}: {e}")
                    raise  # Let the error propagate to fail the test
            
            # Test retrieval
            retrieved_docs = []
            for i in range(len(test_documents)):
                try:
                    doc = await session.memory.retrieve(f"doc_{i}")
                    if doc:
                        retrieved_docs.append(doc)
                except Exception as e:
                    self.logger.error(f"Failed to retrieve document {i}: {e}")
                    raise  # Let the error propagate to fail the test
            
            # Test search functionality
            search_results = []
            search_queries = ["LangSwarm framework", "vector search", "machine learning"]
            
            for query in search_queries:
                try:
                    results = await session.memory.search(
                        query=query,
                        limit=3
                    )
                    search_results.append({
                        "query": query,
                        "results_count": len(results),
                        "results": results[:2]  # Keep first 2 for logging
                    })
                except Exception as e:
                    self.logger.error(f"Search failed for '{query}': {e}")
                    # Let the test fail properly instead of hiding the error
                    raise
            
            # Test cleanup
            await session.close()
            
            return {
                "success": True,
                "storage_backend": "sqlite",
                "documents_stored": stored_count,
                "documents_retrieved": len(retrieved_docs),
                "search_tests": len(search_results),
                "search_results": search_results,
                "memory_operations_functional": stored_count > 0 and len(retrieved_docs) > 0
            }
            
        except Exception as e:
            self.logger.error(f"SQLite memory test failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    async def validate_result(self, result: Dict[str, Any]) -> bool:
        """Validate SQLite memory backend works."""
        if not result.get("success", False):
            return False
        
        if result.get("documents_stored", 0) == 0:
            self.metrics.errors.append("No documents were stored")
            return False
        
        if result.get("documents_retrieved", 0) == 0:
            self.metrics.errors.append("No documents were retrieved")
            return False
        
        return True


class ChromaDBMemoryTest(BaseE2ETest):
    """Test ChromaDB memory backend with vector search."""
    
    @property
    def test_name(self) -> str:
        return "ChromaDB Vector Memory"
    
    @property
    def required_providers(self) -> List[str]:
        return ["openai"]  # For embeddings
    
    @property
    def required_resources(self) -> List[str]:
        return ["chromadb_collection"]
    
    def estimated_cost(self) -> float:
        return 0.03  # Embedding API costs
    
    async def run_test(self) -> Dict[str, Any]:
        """Test ChromaDB with real embeddings."""
        self.logger.info("Testing ChromaDB memory backend")
        
        try:
            import chromadb
            from langswarm.core.session import create_session
            
            # Create session with ChromaDB
            collection_name = f"test_collection_{random.randint(1000, 9999)}"
            
            session = create_session(
                session_id=f"chroma_test_{random.randint(1000, 9999)}",
                memory_backend="chromadb",
                memory_config={
                    "collection_name": collection_name,
                    "embedding_provider": "openai"
                }
            )
            
            # Test documents with different topics
            test_docs = [
                "Artificial intelligence is transforming modern software development practices.",
                "Quantum computing promises exponential speedups for certain algorithmic problems.", 
                "Renewable energy technologies are becoming increasingly cost-effective and efficient.",
                "Blockchain technology enables decentralized consensus without trusted authorities.",
                "Space exploration missions are revealing new insights about planetary formation."
            ]
            
            # Store documents with embeddings
            stored_count = 0
            for i, doc in enumerate(test_docs):
                try:
                    await session.memory.store(
                        key=f"doc_{i}",
                        content=doc,
                        metadata={"topic": ["AI", "quantum", "energy", "blockchain", "space"][i]}
                    )
                    stored_count += 1
                    
                    # Track embedding API call
                    self.track_api_call("openai", tokens=20, cost=0.00002)
                    
                except Exception as e:
                    self.logger.error(f"Failed to store document {i}: {e}")
                    raise  # Let the error propagate
            
            # Test semantic search
            search_tests = [
                "machine learning and AI development",
                "computing performance improvements", 
                "sustainable technology solutions"
            ]
            
            search_results = []
            for query in search_tests:
                try:
                    results = await session.memory.search(
                        query=query,
                        limit=3
                    )
                    
                    # Track embedding API call for query
                    self.track_api_call("openai", tokens=15, cost=0.000015)
                    
                    search_results.append({
                        "query": query,
                        "results_count": len(results),
                        "top_result": results[0] if results else None
                    })
                    
                except Exception as e:
                    self.logger.error(f"Search failed for '{query}': {e}")
                    raise  # Let the error propagate
            
            # Test similarity scores
            similarity_test = None
            if search_results and search_results[0].get("top_result"):
                top_result = search_results[0]["top_result"]
                similarity_test = {
                    "has_similarity_score": "score" in top_result or "distance" in top_result,
                    "result_structure": list(top_result.keys()) if isinstance(top_result, dict) else str(type(top_result))
                }
            
            await session.close()
            
            return {
                "success": True,
                "backend": "chromadb",
                "collection_name": collection_name,
                "documents_stored": stored_count,
                "search_tests_completed": len(search_results),
                "search_results": search_results,
                "similarity_test": similarity_test,
                "embedding_provider": "openai",
                "vector_search_functional": any(r.get("results_count", 0) > 0 for r in search_results)
            }
            
        except ImportError:
            return {
                "success": False,
                "error": "ChromaDB not available",
                "skip_reason": "ChromaDB not installed"
            }
        except Exception as e:
            self.logger.error(f"ChromaDB test failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }


class RedisMemoryTest(BaseE2ETest):
    """Test Redis memory backend with caching and search."""
    
    @property
    def test_name(self) -> str:
        return "Redis Memory Backend"
    
    @property
    def required_providers(self) -> List[str]:
        return []
    
    @property
    def required_resources(self) -> List[str]:
        return ["redis_instance"]
    
    def estimated_cost(self) -> float:
        return 0.0  # No API costs for Redis
    
    async def run_test(self) -> Dict[str, Any]:
        """Test Redis memory operations."""
        self.logger.info("Testing Redis memory backend")
        
        try:
            import redis.asyncio as redis
            
            # Connect to Redis
            redis_url = self.env.config["databases"]["redis_url"]
            client = redis.from_url(redis_url)
            
            # Test basic Redis operations
            test_key = f"langswarm_test_{random.randint(1000, 9999)}"
            test_data = {
                "content": "This is a test document for Redis memory backend",
                "metadata": {"type": "test", "timestamp": "2024-01-01"},
                "embedding": [0.1, 0.2, 0.3, 0.4, 0.5]  # Mock embedding
            }
            
            # Store data
            await client.hset(test_key, mapping={
                "content": test_data["content"],
                "metadata": str(test_data["metadata"]),
                "embedding": str(test_data["embedding"])
            })
            
            # Retrieve data
            retrieved = await client.hgetall(test_key)
            
            # Test TTL
            await client.expire(test_key, 300)  # 5 minute TTL
            ttl = await client.ttl(test_key)
            
            # Test search functionality (if Redis Search is available)
            search_available = False
            try:
                # Try to create a search index
                index_name = f"test_index_{random.randint(1000, 9999)}"
                await client.execute_command(
                    "FT.CREATE", index_name,
                    "ON", "HASH",
                    "PREFIX", "1", "langswarm_test:",
                    "SCHEMA", "content", "TEXT"
                )
                search_available = True
                
                # Clean up index
                await client.execute_command("FT.DROPINDEX", index_name)
                
            except Exception as e:
                self.logger.info(f"Redis Search not available: {e}")
            
            # Test performance
            start_time = asyncio.get_event_loop().time()
            
            # Batch operations
            pipe = client.pipeline()
            for i in range(100):
                pipe.hset(f"perf_test_{i}", "data", f"test_data_{i}")
            await pipe.execute()
            
            # Batch retrieval
            pipe = client.pipeline()
            for i in range(100):
                pipe.hget(f"perf_test_{i}", "data")
            results = await pipe.execute()
            
            end_time = asyncio.get_event_loop().time()
            batch_time = end_time - start_time
            
            # Cleanup
            await client.delete(test_key)
            for i in range(100):
                await client.delete(f"perf_test_{i}")
            
            await client.close()
            
            return {
                "success": True,
                "backend": "redis",
                "redis_url": redis_url,
                "data_stored": len(retrieved) > 0,
                "ttl_functional": ttl > 0,
                "search_available": search_available,
                "batch_operations_time": batch_time,
                "batch_ops_per_second": 200 / batch_time if batch_time > 0 else 0,
                "redis_functional": True
            }
            
        except ImportError:
            return {
                "success": False,
                "error": "Redis not available",
                "skip_reason": "Redis library not installed"
            }
        except Exception as e:
            self.logger.error(f"Redis test failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }


class BigQueryMemoryTest(BaseE2ETest):
    """Test BigQuery memory backend with cloud integration."""
    
    @property
    def test_name(self) -> str:
        return "BigQuery Cloud Memory"
    
    @property
    def required_providers(self) -> List[str]:
        return ["openai"]  # For embeddings
    
    @property
    def required_resources(self) -> List[str]:
        return ["bigquery_dataset"]
    
    def estimated_cost(self) -> float:
        return 0.05  # BigQuery and embedding costs
    
    def should_skip(self) -> str:
        """Check BigQuery prerequisites."""
        skip_reason = super().should_skip()
        if skip_reason:
            return skip_reason
        
        if not self.env.config["cloud"]["gcp_project"]:
            return "No GCP project configured"
        
        if not self.env.config["cloud"]["gcp_credentials"]:
            return "No GCP credentials configured"
        
        return None
    
    async def run_test(self) -> Dict[str, Any]:
        """Test BigQuery memory operations."""
        self.logger.info("Testing BigQuery memory backend")
        
        try:
            from google.cloud import bigquery
            from langswarm.core.session import create_session
            
            # Set up BigQuery dataset
            dataset_id = await self.env.setup_resource("bigquery_dataset")
            
            # Create session with BigQuery backend
            session = create_session(
                session_id=f"bq_test_{random.randint(1000, 9999)}",
                memory_backend="bigquery",
                memory_config={
                    "project": self.env.config["cloud"]["gcp_project"],
                    "dataset": dataset_id,
                    "table": "memory_test",
                    "embedding_provider": "openai"
                }
            )
            
            # Test documents
            test_docs = [
                "Cloud computing enables scalable and flexible infrastructure deployment.",
                "Data warehousing solutions provide centralized analytics capabilities.",
                "Serverless architectures reduce operational overhead and improve scalability."
            ]
            
            # Store documents
            stored_count = 0
            for i, doc in enumerate(test_docs):
                try:
                    await session.memory.store(
                        key=f"cloud_doc_{i}",
                        content=doc,
                        metadata={"category": "cloud_tech", "index": i}
                    )
                    stored_count += 1
                    
                    # Track embedding cost
                    self.track_api_call("openai", tokens=25, cost=0.000025)
                    
                except Exception as e:
                    self.logger.error(f"Failed to store document {i}: {e}")
                    raise  # Let the error propagate
            
            # Test vector search in BigQuery
            search_query = "scalable cloud infrastructure"
            search_results = []
            
            try:
                results = await session.memory.search(
                    query=search_query,
                    limit=5
                )
                
                # Track embedding cost for search
                self.track_api_call("openai", tokens=15, cost=0.000015)
                
                search_results = {
                    "query": search_query,
                    "results_count": len(results),
                    "has_similarity_scores": any("score" in r or "distance" in r for r in results) if results else False
                }
                
            except Exception as e:
                self.logger.error(f"BigQuery search failed: {e}")
                raise  # Let the error propagate
            
            # Test BigQuery-specific features
            client = bigquery.Client(project=self.env.config["cloud"]["gcp_project"])
            
            # Query table directly to verify data
            table_exists = False
            row_count = 0
            
            try:
                table_ref = client.dataset(dataset_id).table("memory_test")
                table = client.get_table(table_ref)
                table_exists = True
                
                # Count rows
                query = f"SELECT COUNT(*) as count FROM `{self.env.config['cloud']['gcp_project']}.{dataset_id}.memory_test`"
                results = client.query(query)
                for row in results:
                    row_count = row.count
                    break
                    
            except Exception as e:
                self.logger.error(f"BigQuery table verification failed: {e}")
                raise  # Let the error propagate
            
            await session.close()
            
            return {
                "success": True,
                "backend": "bigquery",
                "project": self.env.config["cloud"]["gcp_project"],
                "dataset": dataset_id,
                "documents_stored": stored_count,
                "table_exists": table_exists,
                "row_count": row_count,
                "search_results": search_results,
                "vector_search_functional": "error" not in search_results,
                "bigquery_integration_working": table_exists and row_count > 0
            }
            
        except ImportError:
            return {
                "success": False,
                "error": "Google Cloud BigQuery not available",
                "skip_reason": "BigQuery library not installed"
            }
        except Exception as e:
            self.logger.error(f"BigQuery test failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }