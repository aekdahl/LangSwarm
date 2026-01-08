"""
Storage layer for Reflexive Memory lessons.
"""
import logging
import json
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..vector_stores.interfaces import IVectorStore, VectorDocument, VectorQuery, IEmbeddingProvider
from .models import Lesson

logger = logging.getLogger(__name__)

class LessonStore:
    """
    Manages storage and retrieval of Reflexive Memory lessons using a Vector Store.
    """

    def __init__(self, vector_store: IVectorStore, embedding_provider: IEmbeddingProvider, namespace: str = "agent_lessons"):
        self.vector_store = vector_store
        self.embedding_provider = embedding_provider
        self.namespace = namespace

    async def add_lesson(self, lesson: Lesson) -> bool:
        """
        Add a new lesson to the store.
        Embeds the trigger_scenario_text to use as the vector key.
        """
        try:
            # Generate embedding for the trigger scenario (User Query)
            if not lesson.vector:
                lesson.vector = await self.embedding_provider.embed_text(lesson.trigger_scenario_text)

            # Create VectorDocument
            # We map relevant fields to metadata for later retrieval and filtering
            metadata = lesson.to_dict()
            # Remove vector from metadata to save space if needed, though usually fine
            
            doc = VectorDocument(
                id=lesson.lesson_id,
                content=lesson.rule_content, # The content is the rule itself
                embedding=lesson.vector,
                metadata=metadata,
                timestamp=lesson.created_at
            )

            await self.vector_store.upsert_documents([doc])
            logger.info(f"Added lesson {lesson.lesson_id}: {lesson.rule_content[:50]}...")
            return True

        except Exception as e:
            logger.error(f"Failed to add lesson: {e}")
            return False

    async def search_lessons(self, query_text: str, limit: int = 5, threshold: float = 0.85, 
                           scope: Optional[str] = None, target_role: Optional[str] = None) -> List[Lesson]:
        """
        Search for lessons relevant to the query_text.
        Supports filtering by scope and target_role.
        """
        try:
            # Embed the incoming query
            query_vector = await self.embedding_provider.embed_text(query_text)

            # Build filters
            filters = {}
            if scope:
                filters["scope"] = scope
            if target_role:
                filters["target_role"] = target_role

            # Query vector store
            vector_query = VectorQuery(
                embedding=query_vector,
                top_k=limit,
                min_score=threshold,
                filters=filters if filters else None,
                include_metadata=True,
                include_content=True
            )

            results = await self.vector_store.query(vector_query)
            
            lessons = []
            for res in results:
                try:
                    metadata = res.metadata
                    lesson = Lesson.from_dict(metadata)
                    lessons.append(lesson)
                except Exception as e:
                    logger.warning(f"Failed to parse lesson from result {res.id}: {e}")

            return lessons

        except Exception as e:
            logger.error(f"Failed to search lessons: {e}")
            return []

    async def increment_hit_count(self, lesson_id: str):
        """
        Increment the hit count for a retrieved lesson.
        Note: This implementation implies a Read-Modify-Write and might be slow or racy.
        For production, this should ideally be handled by a faster side-channel (Redis) or batch update.
        Here we do a simple implementation for MVP.
        """
        try:
            doc = await self.vector_store.get_document(lesson_id)
            if doc and doc.metadata:
                current_hits = doc.metadata.get("hit_count", 0)
                doc.metadata["hit_count"] = current_hits + 1
                
                # We need to re-upsert
                # Ideally we don't re-embed, but VectorDocument might require existing embedding if not fetched?
                # IVectorStore.get_document usually returns embedding.
                
                await self.vector_store.upsert_documents([doc])
        except Exception as e:
            logger.warning(f"Failed to increment hit count for {lesson_id}: {e}")

    async def get_all_lessons(self) -> List[Lesson]:
        """
        Retrieve all lessons (for Maintenance Path).
        """
        try:
            # Depending on vector store, listing all might be pagination-heavy.
            # Assuming list_documents returns IDs, then fetch.
            # Or use a query with dummy vector if store supports "match all" or metadata filter only.
            
            # This is a naive implementation: list all IDs then get docs.
            # Warning: potentially O(N) memory/time.
            doc_ids = await self.vector_store.list_documents(limit=10000) # Arbitrary high limit
            
            lessons = []
            for doc_id in doc_ids:
                doc = await self.vector_store.get_document(doc_id)
                if doc and doc.metadata:
                    try:
                        lessons.append(Lesson.from_dict(doc.metadata))
                    except:
                        pass
            return lessons
        except Exception as e:
            logger.error(f"Failed to get all lessons: {e}")
            return []

    async def delete_lesson(self, lesson_id: str) -> bool:
        """Delete a lesson."""
        return await self.vector_store.delete_documents([lesson_id])
